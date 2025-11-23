require('dotenv').config();
const { Bot, InputFile } = require('grammy');
const axios = require('axios');
const FormData = require('form-data');

const bot = new Bot(process.env.BOT_API_KEY);

bot.api.setMyCommands([
  { command: 'start', description: 'Запустить бота' },
  { command: 'help', description: 'Информация о боте' }
]);

const MAX_FILE_SIZE = 10 * 1024 * 1024;

// Обработчик документа (PDF-файла)
bot.on('message:document', async(ctx) => {
  try {
    const { document } = ctx.message;

    if (!document.mime_type || !document.mime_type.includes('pdf')) {
      await ctx.reply('✗ Принимаются только PDF-файлы.');
      return;
    }

    if (document.file_size > MAX_FILE_SIZE) {
      await ctx.reply('✗ Файл больше 10 МБ. Сожмите или разделите документ.');
      return;
    }

    const processingMsg = await ctx.reply('⏳ Обрабатываю PDF-файл...');

    const file = await ctx.getFile();
    const fileUrl = `https://api.telegram.org/file/bot${process.env.BOT_API_KEY}/${file.file_path}`;

    const response = await axios({
      method: 'GET',
      url: fileUrl,
      responseType: 'stream'
    });

    const formData = new FormData();
    formData.append('pdf', response.data, {
      filename: document.file_name || 'document.pdf',
      contentType: 'application/pdf'
    });

    const serverResponse = await axios.post(process.env.API_IP, formData, {
      headers: {
        ...formData.getHeaders()
      },
      timeout: 30000
    });

    await ctx.api.deleteMessage(ctx.chat.id, processingMsg.message_id);

    if (serverResponse.data) {
      const jsonString = JSON.stringify(serverResponse.data, null, 2);

      if (jsonString.length > 4000) {
        await ctx.replyWithDocument(new InputFile(
          Buffer.from(jsonString),
          'result.json'
        ), {
          caption: '✅ Результат распознавания PDF:'
        });
      } else {
        await ctx.reply(`✅ Результат распознавания PDF:\n\`\`\`json\n${jsonString}\n\`\`\``, {
          parse_mode: 'Markdown'
        });
      }
    } else {
      await ctx.reply('✅ Файл успешно обработан, но сервер не вернул данные.');
    };
  } catch (error) {
    await handleUploadError(ctx, error);
  }
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

Как использовать:
1. Загрузите PDF-файл с платежным счетом
2. Бот обработает документ
3. Вы получите JSON с распознанной структурой документа

Поддерживаемые форматы: PDF
Максимальный размер: 10 МБ`;

  await ctx.reply(helpText);
});

// Обработка неизвестных команд
bot.on('message', async(ctx) => {
  if (ctx.message.text && !ctx.message.text.startsWith('/')) {
    await ctx.reply('Для работы с ботом используйте команды из меню или загрузите PDF-файл.');
  }
});

// Обработка ошибок
async function handleUploadError(ctx, error) {
  if (error.response) {
    const { status } = error.response;

    switch (status) {
    case 400:
      await ctx.reply('✗ Неверный формат запроса. Убедитесь, что вы отправили PDF-файл.');
      break;
    case 413:
      await ctx.reply('✗ Файл больше 10 МБ. Сожмите или разделите документ.');
      break;
    case 415:
      await ctx.reply('✗ Принимаются только PDF-файлы.');
      break;
    case 429:
      await ctx.reply('✗ Слишком много запросов. Подождите 1 мин и повторите.');
      break;
    case 404:
      await ctx.reply('✗ Результат устарел или не существует. Начните заново.');
      break;
    case 408:
      await ctx.reply('✗ Превышено времени ожидания ответа от ML сервиса');
      break;
    case 500:
      await ctx.reply('✗ Ошибка сервера. Мы уже разбираемся, попробуйте позже.');
      break;
    case 502:
      await ctx.reply('✗ Сервис распознавания временно недоступен. Попробуйте позже.');
      break;
    default:
      await ctx.reply('✗ Произошла ошибка при обработке файла. Попробуйте позже.');
    }
  } else if (error.code === 'ECONNABORTED') {
    await ctx.reply('✗ Превышено времени ожидания ответа от ML сервиса');
  } else {
    await ctx.reply('✗ Произошла неизвестная ошибка. Попробуйте позже.');
  }
}

bot.start();
