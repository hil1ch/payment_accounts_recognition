require('dotenv').config();
const { Bot } = require('grammy');

const bot = new Bot(process.env.BOT_API_KEY);

bot.command('start', async(ctx) => {
  await ctx.reply(
    'Добро пожаловать в сервис для распознания содержимого pdf-скана платёжного счёта!'
  );
});

bot.start();
