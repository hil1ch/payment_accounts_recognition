require('dotenv').config();
const { Bot, GrammyError, HttpError } = require('grammy');

const bot = new Bot(process.env.BOT_API_KEY);

bot.api.setMyCommands([
  { command: 'start', description: 'Запустить бота' },
  { command: 'help', description: 'Информация о боте' }
]);

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

Поддерживаемые форматы: PDF`;

  await ctx.reply(helpText);
});

// Обработка неизвестных команд
bot.on('message', async(ctx) => {
  if (ctx.message.text && !ctx.message.text.startsWith('/')) {
    await ctx.reply('Для работы с ботом используйте команды из меню или загрузите PDF-файл.');
  }
});

// Обработка ошибок
bot.catch((err) => {
  const { ctx } = err;
  console.error(`Error while handling update ${ctx.update.update_id}:`);
  const e = err.error;

  if (e instanceof GrammyError) {
    console.error('Error in request:', e.description);

    // Определяем текст ошибки для пользователя на основе кода
    let errorMessage;
    switch (e.error_code) {
    case 400:
      errorMessage = '✗ Неверный формат запроса. Убедитесь, что вы отправили PDF-файл.';
      break;
    case 413:
      errorMessage = '✗ Файл больше 10 МБ. Сожмите или разделите документ.';
      break;
    case 415:
      errorMessage = '✗ Принимаются только PDF-файлы.';
      break;
    case 429:
      errorMessage = '✗ Слишком много запросов. Подождите 1 мин и повторите.';
      break;
    case 404:
      errorMessage = '✗ Результат устарел или не существует. Начните заново.';
      break;
    case 408:
      errorMessage = '✗ Превышено времени ожидания ответа от ML сервиса';
      break;
    case 500:
      errorMessage = '✗ Ошибка сервера. Мы уже разбираемся, попробуйте позже.';
      break;
    case 502:
      errorMessage = '✗ Сервис распознавания временно недоступен. Попробуйте позже.';
      break;
    default:
      errorMessage = '✗ Произошла неизвестная ошибка. Попробуйте позже.';
    }

    // Отправляем сообщение об ошибке пользователю
    ctx.reply(errorMessage).catch(console.error);
  } else if (e instanceof HttpError) {
    console.error('Could not contact Telegram:', e);
    ctx.reply('✗ Не удалось связаться с сервером. Попробуйте позже.').catch(console.error);
  } else {
    console.error('Unknown error:', e);
    ctx.reply('✗ Произошла неизвестная ошибка. Попробуйте позже.').catch(console.error);
  }
});

bot.start();
