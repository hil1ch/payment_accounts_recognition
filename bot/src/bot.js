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

// Настройка команд
bot.api.setMyCommands([
  { command: 'start', description: 'Запустить бота' },
  { command: 'help', description: 'Информация о боте' }
]);

function getErrorMessage(error) {
  if (error.response) {
    const { status } = error.response;

    switch (status) {
    case 400:
      return 'Неверный формат запроса. Убедитесь, что вы отправили PDF-файл.';
    case 413:
      return 'Файл больше 10 МБ. Сожмите или разделите документ.';
    case 415:
      return 'Принимаются только PDF-файлы.';
    case 429:
      return 'Слишком много запросов. Подождите 1 мин и повторите.';
    case 404:
      return 'Результат устарел или не существует. Начните заново.';
    case 408:
      return 'Превышено времени ожидания ответа от ML сервиса';
    case 500:
      return 'Ошибка сервера. Мы уже разбираемся, попробуйте позже.';
    case 502:
      return 'Сервис распознавания временно недоступен. Попробуйте позже.';
    default:
      return `Произошла ошибка сервера (${status}). Попробуйте позже.`;
    }
  } else if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
    return 'Превышено времени ожидания ответа от ML сервиса';
  } else {
    return 'Произошла неизвестная ошибка. Попробуйте позже.';
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
    } 
    else {
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

// Основной обработчик PDF
bot.on('message:document', async(ctx) => {
  const { document } = ctx.message;
  const fileName = document.file_name || 'document.pdf';

  // 1. Проверка формата
  if (!document.mime_type || !document.mime_type.includes('pdf')) {
    return ctx.reply(`✗ **${fileName}**: Ошибка. Принимаются только PDF.`, { parse_mode: 'Markdown' });
  }

  // 2. Проверка размера
  if (document.file_size > MAX_FILE_SIZE) {
    return ctx.reply(`✗ **${fileName}**: Ошибка. Файл слишком большой (>10МБ).`, { parse_mode: 'Markdown' });
  }

  // 3. Отправляем сообщение о принятии
  const totalQueueSize = queue.size + queue.pending;
  if (totalQueueSize >= MAX_QUEUE_LENGTH) {
    return ctx.reply(
      `❌ **${fileName}**: Ошибка. Общая очередь переполнена. Сейчас обрабатывается/ожидает **${totalQueueSize}** файлов (лимит: ${MAX_QUEUE_LENGTH}). Попробуйте отправить файлы позже.`,
      {
        parse_mode: 'Markdown',
        reply_to_message_id: ctx.message.message_id
      }
    );
  }

  // 4. Отправляем сообщение о принятии
  const filesInQueue = queue.size + queue.pending;
  const statusText = filesInQueue >= CONCURRENCY_LIMIT
    ? `📥 **${fileName}**: Принят в очередь... (${filesInQueue} в ожидании)`
    : `⚙️ **${fileName}**: Начинаю обработку...`;

  const statusMsg = await ctx.reply(statusText, {
    parse_mode: 'Markdown',
    reply_to_message_id: ctx.message.message_id
  });

  // 5. Добавляем задачу в очередь на выполнение
  queue.add(async() => {
    try {
      // Статус: В работе
      await ctx.api.editMessageText(ctx.chat.id, statusMsg.message_id, `⚙️ **${fileName}**: В работе...`, { parse_mode: 'Markdown' });

      // Скачивание файла из Telegram
      const file = await ctx.getFile();
      const fileUrl = `https://api.telegram.org/file/bot${process.env.BOT_API_KEY}/${file.file_path}`;

      const fileStream = await axios({
        method: 'GET',
        url: fileUrl,
        responseType: 'stream'
      });

      const formData = new FormData();
      formData.append('file', fileStream.data, {
        filename: fileName,
        contentType: 'application/pdf'
      });

      // Запрос к серверу распознавания
      const serverResponse = await axios.post(
        `${process.env.BASE_URL}/parse`,
        formData,
        {
          headers: { ...formData.getHeaders() },
          timeout: Number(process.env.POST_TIMEOUT)
        }
      );

      let parseResponse = serverResponse.data;

      if (typeof parseResponse === 'string') {
        try {
          parseResponse = JSON.parse(parseResponse);
        } catch (e) {
          throw new Error('Невозможно распарсить ответ сервера');
        }
      }

      const jobId = parseResponse?.job_id;
      console.log(jobId);

      if (!jobId) {
        throw new Error('Сервер не вернул job_id');
      }

      // Обновляем статус: ожидание результата
      await ctx.api.editMessageText(
        ctx.chat.id,
        statusMsg.message_id,
        `⏳ **${fileName}**: Распознавание выполняется...`,
        { parse_mode: 'Markdown' }
      );

      // Polling результата
      const resultJson = await pollResult(jobId);

      // Готово
      await ctx.api.editMessageText(
        ctx.chat.id,
        statusMsg.message_id,
        `✅ **${fileName}**: Обработка завершена!`,
        { parse_mode: 'Markdown' }
      );

      // Отправка результата пользователю
      const jsonString = JSON.stringify(resultJson, null, 2);

      if (jsonString.length > 4000) {
        await ctx.replyWithDocument(
          new InputFile(Buffer.from(jsonString), `result_${fileName}.json`),
          { caption: `📄 Результат для: ${fileName}` }
        );
      } else {
        await ctx.reply(
          `📄 **Результат (${fileName}):**\n\`\`\`json\n${jsonString}\n\`\`\``,
          { parse_mode: 'Markdown' }
        );
      }
    } catch (error) {
      console.error(`Ошибка при обработке ${fileName}:`, error.message);
      const errorText = getErrorMessage(error);

      // Обновляем статус: Ошибка
      await ctx.api.editMessageText(ctx.chat.id, statusMsg.message_id, `❌ **${fileName}**: Ошибка\n_${errorText}_`, {
        parse_mode: 'Markdown'
      });
    }
  });
});

// Команда /'start'
bot.command('start', async(ctx) => {
  const welcomeText = `Добро пожаловать в сервис для распознания содержимого pdf-скана платёжного счёта!

Доступные команды:
/start - Запустить бота
/help - Информация о боте

Просто загрузите PDF-файл для распознавания.`;

  await ctx.reply(welcomeText);
});

// Команда /'help'
bot.command('help', async(ctx) => {
  const helpText = `Сервис предоставляет функционал распознавания содержимого pdf-скана платёжного счёта.

Бот поддерживает пакетную загрузку. Просто выделите несколько файлов и отправьте их разом. Я добавлю их в очередь и обработаю один за другим.

Как использовать:
1. Загрузите PDF-файл с платежным счетом
2. Бот обработает документ
3. Вы получите JSON с распознанной структурой документа

Поддерживаемые форматы: PDF
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
