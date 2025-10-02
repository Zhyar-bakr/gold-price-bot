import os
import requests
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
from datetime import datetime
import time
from threading import Thread

# ڕێکخستنی لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# وەرگرتنی تووکن
BOT_TOKEN = os.environ.get('BOT_TOKEN')
DOLLAR_TO_DINAR = 1450

class GoldPriceBot:
    def __init__(self):
        self.updater = Updater(BOT_TOKEN, use_context=True)
        self.dispatcher = self.updater.dispatcher
        self.subscribed_users = set()
        
        self.setup_handlers()
        logger.info("🤖 بۆتی نرخی زێر دەست بە کار دەکات...")
    
    def setup_handlers(self):
        self.dispatcher.add_handler(CommandHandler("start", self.start))
        self.dispatcher.add_handler(CommandHandler("price", self.get_gold_price))
        self.dispatcher.add_handler(CommandHandler("subscribe", self.subscribe))
        self.dispatcher.add_handler(CommandHandler("unsubscribe", self.unsubscribe))
        self.dispatcher.add_handler(CommandHandler("setdollar", self.set_dollar_rate))
        
        self.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_message))
    
    def get_gold_prices_from_api(self):
        try:
            # نرخی نمونەیی - دواتر دەتوانیت API ڕاستی زیاد بکەیت
            import random
            base_price = 1950.75
            change = random.uniform(-20, 20)
            
            return {
                'ounce_usd': round(base_price + change, 2),
                'change': round(change, 2),
                'success': True
            }
        except Exception as e:
            logger.error(f"هەڵە لە وەرگرتنی نرخی زێر: {e}")
            return {'success': False}
    
    def calculate_gold_prices(self, ounce_price_usd):
        gram_price_usd = ounce_price_usd / 31.1035
        meskal_gram = 5
        
        prices = {
            '24k': {
                'iqd_per_meskal': (gram_price_usd * meskal_gram) * DOLLAR_TO_DINAR
            },
            '22k': {
                'iqd_per_meskal': ((gram_price_usd * 0.916) * meskal_gram) * DOLLAR_TO_DINAR
            },
            '21k': {
                'iqd_per_meskal': ((gram_price_usd * 0.875) * meskal_gram) * DOLLAR_TO_DINAR
            },
            '18k': {
                'iqd_per_meskal': ((gram_price_usd * 0.750) * meskal_gram) * DOLLAR_TO_DINAR
            }
        }
        return prices
    
    def format_price_message(self, gold_data):
        if not gold_data['success']:
            return "❌ هەڵە ڕوویدا لە وەرگرتنی نرخەکان"
        
        ounce_price = gold_data['ounce_usd']
        change = gold_data['change']
        
        change_icon = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"
        calculated_prices = self.calculate_gold_prices(ounce_price)
        
        message = f"""
🏅 **نرخی زێر**

{change_icon} **نرخی ئۆنسە:** {ounce_price:,.2f} USD
📈 **گۆڕان:** {change:+,.2f} USD

**نرخی مەسقاڵ (5 گرام) بە دینار:**

🟡 عەیاری ٢٤: {calculated_prices['24k']['iqd_per_meskal']:,.0f} دینار
🟠 عەیاری ٢٢: {calculated_prices['22k']['iqd_per_meskal']:,.0f} دینار  
🔴 عەیاری ٢١: {calculated_prices['21k']['iqd_per_meskal']:,.0f} دینار
🔵 عەیاری ١٨: {calculated_prices['18k']['iqd_per_meskal']:,.0f} دینار

💵 **نرخی دۆلار:** 1 USD = {DOLLAR_TO_DINAR:,.0f} دینار

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        return message
    
    def start(self, update, context):
        user = update.effective_user
        welcome_text = f"""
سڵاو {user.first_name}! 👋

من بۆتی نرخی زێرم.

**فەرمانەکان:**
/price - نرخی ئێستای زێر
/subscribe - بەشداریکردن
/unsubscribe - کۆتایی بە بەشداری
/setdollar - گۆڕینی نرخی دۆلار

🔄 نرخەکان هەر جارێک دەتوانیت بە /price وەریبگریت
        """
        update.message.reply_text(welcome_text)
        logger.info(f"بەکارهێنەری نوێ: {user.first_name}")
    
    def get_gold_price(self, update, context):
        gold_data = self.get_gold_prices_from_api()
        message = self.format_price_message(gold_data)
        update.message.reply_text(message, parse_mode='Markdown')
        logger.info(f"نرخ نێردرا بۆ: {update.effective_user.id}")
    
    def subscribe(self, update, context):
        user_id = update.effective_user.id
        self.subscribed_users.add(user_id)
        update.message.reply_text("✅ بەشداریت کراوە! بە /price نرخەکان وەربگرە")
        logger.info(f"بەشداربووی نوێ: {user_id}")
    
    def unsubscribe(self, update, context):
        user_id = update.effective_user.id
        if user_id in self.subscribed_users:
            self.subscribed_users.remove(user_id)
        update.message.reply_text("❌ بەشداریت هەڵوەشێنرایەوە.")
        logger.info(f"بەشداربوو لابردرا: {user_id}")
    
    def set_dollar_rate(self, update, context):
        if context.args:
            try:
                global DOLLAR_TO_DINAR
                DOLLAR_TO_DINAR = float(context.args[0])
                update.message.reply_text(f"✅ نرخی دۆلار گۆڕدرا بۆ: {DOLLAR_TO_DINAR:,.0f} دینار")
                logger.info(f"نرخی دۆلار گۆڕدرا بۆ: {DOLLAR_TO_DINAR}")
            except ValueError:
                update.message.reply_text("❌ تکایە نرخی دروست بنووسە (نموونە: /setdollar 1450)")
        else:
            update.message.reply_text("❌ تکایە نرخی دۆلار بنووسە (نموونە: /setdollar 1450)")
    
    def handle_message(self, update, context):
        text = update.message.text.lower()
        if any(word in text for word in ["زێر", "نرخ", "gold", "price"]):
            self.get_gold_price(update, context)
        else:
            update.message.reply_text("🤔 تکایە /start بەکاربێنە بۆ زانینی فەرمانەکان.")
    
    def run(self):
        self.updater.start_polling()
        logger.info("✅ بۆت بە سەرکەوتوویی دەستیپێکرد")
        self.updater.idle()

if __name__ == "__main__":
    if BOT_TOKEN:
        bot = GoldPriceBot()
        bot.run()
    else:
        logger.error("❌ تووکنی بۆت دەست نەکەوت!")
