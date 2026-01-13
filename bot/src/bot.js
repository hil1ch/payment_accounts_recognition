require('dotenv').config();
const { Bot, InputFile } = require('grammy');
const axios = require('axios');
const FormData = require('form-data');
const { default: PQueue } = require('p-queue');

const bot = new Bot(process.env.BOT_API_KEY);

// Инициализация очереди
const CONCURRENCY_LIMIT = 1;
const MAX_QUEUE_LENGTH = 10;
const queue = new PQueue({ concurrency: CONCURRENCY_LIMIT });

const MAX_FILE_SIZE = 10 * 1024 * 1024;

const SUPPORTED_MIME_TYPES = new Set([
  'application/pdf',
  'application/x-pdf',
  'image/png',
  'image/jpeg',
  'image/jpg'
]);

async function downloadWithRetry(url, retries = 3, delayMs = 2000) {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      console.log(`[СКАЧИВАНИЕ] Попытка ${attempt}/${retries} для ${url.replace(process.env.BOT_API_KEY, '***СКРЫТ***')}`);
      return await axios({
        method: 'GET',
        url,
        responseType: 'stream',
        timeout: 45000 // 45 секунд на попытку
      });
    } catch (error) {
      console.warn(`[СКАЧИВАНИЕ] Попытка ${attempt} провалена:`, error.message);
      if (attempt === retries) throw error;
      await new Promise(resolve => setTimeout(resolve, delayMs * attempt));
    }
  }
}

function escapeHtml(text) {
  if (!text) return '';
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// Настройка команд
bot.api.setMyCommands([
  { command: 'start', description: 'Запустить бота' },
  { command: 'help', description: 'Информация о боте' }
]);

function getErrorMessage(error) {
  // Логируем детали для отладки (только в консоль, не для пользователя)
  console.error('[DEBUG] Ошибка:', {
    message: error.message || 'Без сообщения',
    code: error.code || 'Нет кода',
    status: error.response?.status,
    url: error.config?.url
  });

  try {
    // 1. Специфичные ошибки Telegram API
    if (error.description) {
      const cleanDesc = error.description
        .replace(/<[^>]*>/g, '')
        .replace(/[*_`[\]()~>#+\-=|{}.!]/g, ' ')
        .trim();

      if (cleanDesc.includes('file must be non-empty')) {
        return 'Файл пустой. Пожалуйста, отправьте документ с содержимым.';
      }
      if (cleanDesc.includes('file is too big')) {
        return 'Файл превышает максимально допустимый размер для Telegram (20 МБ).';
      }
      return `Ошибка Telegram: ${cleanDesc.substring(0, 100)}`;
    }

    // 2. HTTP-ошибки от сервера
    if (error.response) {
      const { status, data } = error.response;
      let serverMessage = '';

      // Извлекаем понятное сообщение из ответа сервера
      if (data) {
        serverMessage = data.detail || data.message || data.error || '';
        if (typeof serverMessage === 'object') serverMessage = JSON.stringify(serverMessage);
      }

      // Чистим от HTML и спецсиволов для Telegram
      serverMessage = (serverMessage + '')
        .replace(/<[^>]*>/g, '')
        .replace(/[*_`[\]()~>#+\-=|{}.!]/g, ' ')
        .trim()
        .substring(0, 150);

      // Обработка конкретных HTTP-статусов
      switch (status) {
        case 400: return serverMessage || 'Неверный формат файла. Принимаются только PDF, PNG или JPEG.';
        case 413: return 'Файл слишком большой. Максимальный размер — 10 МБ.';
        case 415: return 'Неподдерживаемый формат файла. Принимаются только PDF, PNG или JPEG.';
        case 429: return 'Слишком много запросов. Пожалуйста, подождите 1 минуту.';
        case 404: return 'Результат распознавания утерян. Отправьте файл заново.';
        case 408:
        case 504:
          return 'Сервис распознавания не отвечает. Попробуйте позже.';
        case 500: return 'Внутренняя ошибка сервера. Мы уже разбираемся.';
        case 502:
        case 503: return 'Сервис временно недоступен. Повторите попытку через 5 минут.';
        default: return serverMessage
          ? `Сервер вернул ошибку ${status}: ${serverMessage}`
          : `Ошибка обработки (${status}). Попробуйте позже.`;
      }
    }
    if (error.config?.url?.includes('api.telegram.org')) {
        return 'Ошибка загрузки файла из Telegram. Попробуйте отправить файл заново.';
    }

    // 3. Сетевые ошибки и таймауты
    const errorCode = error.code?.toUpperCase() || '';
    const errorMessage = (error.message || '').toLowerCase();

    // Группируем все сетевые ошибки
    if (
      errorCode.includes('ETIME') || // ETIMEDOUT, ESOCKETTIMEDOUT
      errorCode.includes('ECONN') ||  // ECONNREFUSED, ECONNABORTED
      errorCode === 'ENOTFOUND' ||    // DNS error
      errorMessage.includes('timeout') ||
      errorMessage.includes('timed out')
    ) {
      // Разные сообщения для разных этапов обработки
      if (error.config?.url?.includes('/parse')) {
        return 'Не удалось отправить файл на распознавание. Сервер не отвечает.';
      }
      if (error.config?.url?.includes('/result')) {
        return 'Результат распознавания недоступен. Возможно, задача устарела.';
      }
      return 'Проблема с подключением к сервису распознавания. Попробуйте позже.';
    }

    // 4. Ошибки файловой системы
    if (errorCode === 'ENOENT') {
      return 'Файл не найден на сервере. Пожалуйста, отправьте его заново.';
    }

    // 5. Финальное сообщение
    const fallback = (error.message || 'Неизвестная ошибка')
      .replace(/<[^>]*>/g, '')
      .replace(/\n/g, ' ')
      .substring(0, 100);

    return `Ошибка обработки: ${fallback}. Попробуйте отправить файл через 1-2 минуты.`;

  } catch (e) {
    console.error('[CRITICAL] Ошибка в обработчике ошибок:', e);
    return 'Критическая ошибка системы.';
  }
}

async function pollResult(jobId, options = {}) {
  const {
    interval = Number(process.env.POLL_INTERVAL),
    timeout = Number(process.env.POLL_TIMEOUT)
  } = options;

  const startTime = Date.now();

  while (true) {
    const response = await axios.get(
      `${process.env.BASE_URL}/result/${jobId}`,
      { timeout: Number(process.env.GET_TIMEOUT) }
    );

    console.log('POLL:', response.data);

    // eslint-disable-next-line prefer-destructuring
    const data = response.data;

    if (!data || !data.status) {
      throw new Error('Некорректный ответ сервера');
    }

    // ✅ Готово
    if (data.status === 'done') {
      return data;
    }

    // ⏳ В ожидании
    if (data.status === 'waiting' || data.status === 'in_progress') {
      // ничего не делаем
    } else {
      throw new Error(`Неизвестный статус задачи: ${data.status}`);
    }

    if (Date.now() - startTime > timeout) {
      const err = new Error('Timeout while waiting for recognition result');
      err.code = 'TIMEOUT';
      throw err;
    }

    await new Promise(resolve => setTimeout(resolve, interval));
  }
}

// Основной обработчик файлов
async function handleFileMessage(ctx, fileMeta) {
  console.log(`[НАЧАЛО] Начало обработки файла. Chat ID: ${ctx.chat.id}, Message ID: ${ctx.message.message_id}`);

  const {
    rawFileName,
    mimeType,
    fileSize
  } = fileMeta;
  const fileName = rawFileName || 'document.pdf';
  console.log(`[ФАЙЛ] Имя: ${fileName}, MIME: ${mimeType}, Размер: ${fileSize} байт`);

  const safeFileName = escapeHtml(fileName);

  // 1. Проверка формата
  console.log(`[ПРОВЕРКА] Проверка формата файла...`);
  if (!mimeType || !SUPPORTED_MIME_TYPES.has(mimeType)) {
    console.warn(`[ОШИБКА] Неподдерживаемый MIME-тип: ${mimeType} для файла ${fileName}`);
    return ctx.reply(`❌ <b>${safeFileName}</b>: Ошибка. Принимаются только PDF/PNG/JPEG.`, { parse_mode: 'HTML' });
  }
  console.log(`[УСПЕХ] Формат файла поддерживается: ${mimeType}`);

  // 2. Проверка размера
  console.log(`[ПРОВЕРКА] Проверка размера файла...`);
  if (fileSize > MAX_FILE_SIZE) {
    console.warn(`[ОШИБКА] Файл слишком большой: ${fileSize} байт (максимум ${MAX_FILE_SIZE})`);
    return ctx.reply(`❌ <b>${safeFileName}</b>: Ошибка. Файл слишком большой (&gt;10МБ).`, { parse_mode: 'HTML' });
  }
  console.log(`[УСПЕХ] Размер файла в пределах нормы`);

  // 3. Проверка очереди
  const totalQueueSize = queue.size + queue.pending;
  console.log(`[ОЧЕРЕДЬ] Текущий размер очереди: ${queue.size}, обрабатывается: ${queue.pending}, всего: ${totalQueueSize}`);

  if (totalQueueSize >= MAX_QUEUE_LENGTH) {
    console.warn(`[ОШИБКА] Очередь переполнена: ${totalQueueSize} >= ${MAX_QUEUE_LENGTH}`);
    return ctx.reply(
      `❌ <b>${escapeHtml(fileName)}</b>: Ошибка. Общая очередь переполнена. Сейчас обрабатывается/ожидает <b>${totalQueueSize}</b> файлов (лимит: ${MAX_QUEUE_LENGTH}). Попробуйте позже.`,
      {
        parse_mode: 'HTML',
        reply_to_message_id: ctx.message.message_id
      }
    );
  }

  // 4. Отправка статусного сообщения
  const filesInQueue = queue.size + queue.pending;
  const statusText = filesInQueue >= CONCURRENCY_LIMIT
    ? `📥 <b>${safeFileName}</b>: Принят в очередь... (${filesInQueue} в ожидании)`
    : `⚙️ <b>${safeFileName}</b>: Начинаю обработку...`;

  console.log(`[СТАТУС] Отправка сообщения: "${statusText.replace(/<[^>]*>/g, '')}"`);
  const statusMsg = await ctx.reply(statusText, {
    parse_mode: 'HTML',
    reply_to_message_id: ctx.message.message_id
  });
  console.log(`[СТАТУС] Сообщение отправлено. Message ID: ${statusMsg.message_id}`);

  queue.add(async () => {
    console.log(`[ОЧЕРЕДЬ] Задача добавлена в очередь. Job ID: ${Date.now()}_${ctx.message.message_id}`);

    try {
      // Статус: В работе
      console.log(`[СТАТУС] Обновление статуса: "В работе"`);
      await ctx.api.editMessageText(
        ctx.chat.id,
        statusMsg.message_id,
        `⚙️ <b>${escapeHtml(fileName)}</b>: В работе...`,
        { parse_mode: 'HTML' }
      );
      console.log(`[СТАТУС] Статус успешно обновлён`);

      // Скачивание файла из Telegram
      console.log(`[ТЕЛЕГРАМ] Получение информации о файле...`);
      const file = await ctx.getFile();
      console.log(`[ТЕЛЕГРАМ] Файл найден. File ID: ${file.file_id}, Путь: ${file.file_path}`);

      // ИСПРАВЛЕНИЕ: Убран лишний пробел в URL
      const fileUrl = `https://api.telegram.org/file/bot${process.env.BOT_API_KEY}/${file.file_path}`;
      console.log(`[ТЕЛЕГРАМ] URL для скачивания: ${fileUrl.replace(process.env.BOT_API_KEY, '***СКРЫТ***')}`);

      console.log(`[СКАЧИВАНИЕ] Начало загрузки файла из Telegram...`);
      const fileStream = await downloadWithRetry(fileUrl, 6, 3000);
      console.log(`[СКАЧИВАНИЕ] Файл успешно загружен из Telegram`);

      // Подготовка формы
      console.log(`[ОТПРАВКА] Подготовка FormData для отправки на ML-сервис`);
      const formData = new FormData();
      formData.append('file', fileStream.data, {
        filename: fileName,
        contentType: mimeType
      });

      // Отправка на сервер распознавания
      const parseUrl = `${process.env.BASE_URL}/parse`;
      console.log(`[ML-СЕРВИС] Отправка файла на ${parseUrl.replace(/\/\/[^/]+/, '//***')}. Размер: ${fileSize} байт`);

      const serverResponse = await axios.post(parseUrl, formData, {
        headers: { ...formData.getHeaders() },
        timeout: Number(process.env.POST_TIMEOUT)
      });
      console.log(`[ML-СЕРВИС] Успешный ответ. Статус: ${serverResponse.status}, Job ID: ${serverResponse.data?.job_id}`);

      let parseResponse = serverResponse.data;
      if (typeof parseResponse === 'string') {
        console.log(`[ML-СЕРВИС] Ответ в формате строки. Попытка парсинга JSON`);
        parseResponse = JSON.parse(parseResponse);
      }

      const jobId = parseResponse?.job_id;
      if (!jobId) {
        console.error(`[КРИТИЧЕСКАЯ ОШИБКА] Сервер не вернул job_id. Ответ:`, parseResponse);
        throw new Error('Сервер не вернул job_id');
      }
      console.log(`[ML-СЕРВИС] Получен Job ID: ${jobId}`);

      // Статус: в ожидании результата
      console.log(`[СТАТУС] Обновление статуса: "Распознавание выполняется"`);
      await ctx.api.editMessageText(
        ctx.chat.id,
        statusMsg.message_id,
        `⏳ <b>${escapeHtml(fileName)}</b>: Распознавание выполняется...`,
        { parse_mode: 'HTML' }
      );

      // Опрос результата
      console.log(`[ML-СЕРВИС] Начало опроса результата. Job ID: ${jobId}`);
      const resultJson = await pollResult(jobId);
      console.log(`[ML-СЕРВИС] Результат получен. Размер данных: ${JSON.stringify(resultJson).length} байт`);

      // Статус: готово
      console.log(`[СТАТУС] Обновление статуса: "Обработка завершена"`);
      await ctx.api.editMessageText(
        ctx.chat.id,
        statusMsg.message_id,
        `✅ <b>${escapeHtml(fileName)}</b>: Обработка завершена!`,
        { parse_mode: 'HTML' }
      );

      // Отправка результата
      const jsonString = JSON.stringify(resultJson, null, 2);
      console.log(`[РЕЗУЛЬТАТ] Отправка результата пользователю. Размер JSON: ${jsonString.length} байт`);

      if (jsonString.length > 4000) {
        console.log(`[ОТПРАВКА] Файл слишком большой. Отправка как документа`);
        await ctx.replyWithDocument(
          new InputFile(Buffer.from(jsonString), `result_${fileName}.json`),
          { caption: `📄 Результат для: ${fileName}` }
        );
      } else {
        console.log(`[ОТПРАВКА] Отправка как текстового сообщения`);
        await ctx.reply(
          `📄 <b>Результат (${safeFileName}):</b>\n<pre>${escapeHtml(jsonString)}</pre>`,
          { parse_mode: 'HTML' }
        );
      }
      console.log(`[ЗАВЕРШЕНИЕ] Обработка файла успешно завершена`);

    } catch (error) {
      console.error(`[КРИТИЧЕСКАЯ ОШИБКА] Файл: ${fileName}, Chat ID: ${ctx.chat.id}`, {
        message: error.message,
        stack: error.stack,
        code: error.code,
        config: error.config ? {
          url: error.config.url,
          method: error.config.method
        } : undefined
      });

      const errorText = getErrorMessage(error);
      console.log(`[ОБРАБОТКА ОШИБКИ] Понятное сообщение для пользователя: "${errorText}"`);

      try {
        // Безопасное обновление статуса с экранированием
        await ctx.api.editMessageText(
          ctx.chat.id,
          statusMsg.message_id,
          `❌ <b>${escapeHtml(fileName)}</b>: Ошибка\n<i>${escapeHtml(errorText)}</i>`,
          { parse_mode: 'HTML' }
        );
        console.log(`[СТАТУС] Статус ошибки успешно отправлен`);
      } catch (telegramError) {
        console.error(`[ОШИБКА TELEGRAM] Не удалось отправить сообщение об ошибке:`, telegramError.message);
        // Резервный вариант
        try {
          await ctx.reply(`❌ КРИТИЧЕСКАЯ ОШИБКА обработки ${fileName}:\n${errorText}`);
        } catch (finalError) {
          console.error(`[ПОЛНЫЙ ПРОВАЛ] Не удалось уведомить пользователя об ошибке:`, finalError);
        }
      }
    }
  });

  console.log(`[ОЧЕРЕДЬ] Задача передана в обработку. Текущий размер очереди: ${queue.size}, обрабатывается: ${queue.pending}`);
}

// Основной обработчик PDF/PNG/JPEG как документ
bot.on('message:document', async(ctx) => {
  const { document } = ctx.message;
  const rawFileName = document.file_name || 'document';
  const mimeType = document.mime_type;
  const fileSize = document.file_size;

  await handleFileMessage(ctx, { rawFileName, mimeType, fileSize });
});

// Обработчик изображений, отправленных как фото
bot.on('message:photo', async(ctx) => {
  const { photo } = ctx.message;
  if (!photo || photo.length === 0) {
    return;
  }

  const largestPhoto = photo[photo.length - 1];
  const rawFileName = `photo_${ctx.message.message_id}.jpg`;
  const mimeType = 'image/jpeg';
  const fileSize = largestPhoto.file_size;

  await handleFileMessage(ctx, { rawFileName, mimeType, fileSize });
});

// Команда /'start'
bot.command('start', async(ctx) => {
  const welcomeText = `Добро пожаловать в сервис для распознания содержимого скана платёжного счёта!

Доступные команды:
/start - Запустить бота
/help - Информация о боте

Просто загрузите PDF/PNG/JPEG-файл для распознавания.`;

  await ctx.reply(welcomeText);
});

// Команда /'help'
bot.command('help', async(ctx) => {
  const helpText = `Сервис предоставляет функционал распознавания содержимого скана платёжного счёта.

Бот поддерживает пакетную загрузку. Просто выделите несколько файлов и отправьте их разом. Я добавлю их в очередь и обработаю один за другим.

Как использовать:
1. Загрузите PDF/PNG/JPEG-файл с платежным счетом
2. Бот обработает документ
3. Вы получите JSON с распознанной структурой документа

Поддерживаемые форматы: PDF, PNG, JPEG
Максимальный размер: 10 МБ`;

  await ctx.reply(helpText);
});

if (require.main === module) {
  bot.start();
}

// Экспортируем функцию для тестирования
module.exports = {
  getErrorMessage
// eslint-disable-next-line semi
}
