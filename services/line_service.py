from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, 
    ImageMessage, TemplateSendMessage, ButtonsTemplate, 
    URIAction, MessageAction
)
import os

class LineService:
    def __init__(self):
        """Initialize LINE API client"""
        self.line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
        self.handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))
        self.liff_id = os.getenv('LIFF_ID')
        
        # Register message handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register message event handlers"""
        @self.handler.add(MessageEvent, message=TextMessage)
        def handle_text_message(event):
            """Handle text messages"""
            text = event.message.text
            user_id = event.source.user_id
            
            if text == "アンケート":
                # Send LIFF app button
                buttons_template = ButtonsTemplate(
                    title='こども食堂アンケート',
                    text='アンケート用紙の写真を撮影してください',
                    actions=[
                        URIAction(
                            label='カメラを起動',
                            uri=f"https://liff.line.me/{self.liff_id}"
                        )
                    ]
                )
                
                template_message = TemplateSendMessage(
                    alt_text='アンケート',
                    template=buttons_template
                )
                
                self.line_bot_api.reply_message(
                    event.reply_token,
                    template_message
                )
            elif text == "ヘルプ":
                # Send help message
                help_message = (
                    "【使い方】\n"
                    "1. 「アンケート」と送信すると、カメラ起動ボタンが表示されます\n"
                    "2. ボタンをタップしてカメラを起動し、アンケート用紙を撮影します\n"
                    "3. 撮影した画像を送信すると、自動的に集計されます\n\n"
                    "【コマンド】\n"
                    "・アンケート：カメラを起動\n"
                    "・ヘルプ：このヘルプを表示"
                )
                
                self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=help_message)
                )
            else:
                # Default message
                self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="「アンケート」と送信すると、カメラを起動できます")
                )
    
    def handle_webhook(self, body, signature):
        """Handle LINE webhook"""
        try:
            self.handler.handle(body, signature)
        except InvalidSignatureError:
            raise ValueError("Invalid signature")
    
    def get_profile(self, user_id):
        """Get user profile from LINE"""
        return self.line_bot_api.get_profile(user_id)
    
    def send_survey_result(self, user_id, counts, user_profile):
        """Send survey results via LINE message"""
        # Format results
        message = "アンケート集計結果\n\n"
        
        quadrant_names = {
            'UL': '左上',
            'UR': '右上',
            'LL': '左下',
            'LR': '右下'
        }
        
        color_names = {
            'red': '赤',
            'green': '緑',
            'blue': '青',
            'yellow': '黄'
        }
        
        # Count totals by quadrant and color
        for quadrant, colors in counts.items():
            message += f"【{quadrant_names[quadrant]}】\n"
            
            for color, count in colors.items():
                if count > 0:
                    message += f"・{color_names[color]}: {count}個\n"
            
            message += "\n"
        
        # Send message
        self.line_bot_api.push_message(
            user_id,
            TextSendMessage(text=message)
        )
