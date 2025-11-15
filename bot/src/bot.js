require('dotenv').config();
const { Bot } = require('grammy');

const bot = new Bot(process.env.BOT_API_KEY);

bot.api.setMyCommands([
  { command: 'start', description: 'Запустить бота' },
  { command: 'help', description: 'Информация о боте' }
]);

bot.command('start', async(ctx) => {
  const welcomeText = `Добро пожаловать в сервис для распознания содержимого pdf-скана платёжного счёта!

Доступные команды:
/start - Запустить бота
/help - Информация о боте

Просто загрузите PDF-файл для распознавания.`;

  await ctx.reply(welcomeText);
});

bot.command('help', async(ctx) => {
  await ctx.reply(
    'Сервис предоставляет функционал распознавания содержимого pdf-скана платёжного счёта. Вы загружаете файл - бот возвращает JSON с распозанной структурой документа'
  );
});

bot.start();
