from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import json
import logging
from chatbot_with_model import HandbookChatbot

# Thiết lập logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ActionHandbookQuery(Action):
    """Action để trả lời câu hỏi về sổ tay sinh viên"""
    
    def __init__(self):
        super().__init__()
        self.chatbot = None
        self._load_chatbot()
    
    def _load_chatbot(self):
        """Tải chatbot handbook"""
        try:
            self.chatbot = HandbookChatbot()
            self.chatbot.load_model()
            
            # Thử tải index đã có
            if not self.chatbot.load_index():
                # Tạo index mới nếu chưa có
                chunks = self.chatbot.parse_handbook("handbook_summary.txt")
                self.chatbot.create_embeddings(chunks)
                self.chatbot.save_index()
            
            logger.info("Handbook chatbot đã được tải thành công!")
        except Exception as e:
            logger.error(f"Lỗi khi tải handbook chatbot: {e}")
            self.chatbot = None
    
    def name(self) -> str:
        return "action_handbook_query"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list:
        """Xử lý câu hỏi về sổ tay sinh viên"""
        
        if self.chatbot is None:
            dispatcher.utter_message(text="Xin lỗi, hệ thống handbook đang gặp sự cố. Vui lòng thử lại sau.")
            return []
        
        # Lấy câu hỏi từ user
        user_message = tracker.latest_message.get('text', '')
        
        if not user_message:
            dispatcher.utter_message(text="Xin lỗi, tôi không hiểu câu hỏi của bạn. Vui lòng hỏi lại.")
            return []
        
        try:
            # Tìm kiếm câu trả lời
            answer = self.chatbot.answer_question(user_message)
            
            # Gửi câu trả lời
            dispatcher.utter_message(text=answer)
            
            # Lưu thông tin về câu hỏi đã được trả lời
            return [SlotSet("last_handbook_query", user_message)]
            
        except Exception as e:
            logger.error(f"Lỗi khi xử lý câu hỏi handbook: {e}")
            dispatcher.utter_message(text="Xin lỗi, có lỗi xảy ra khi tìm kiếm thông tin. Vui lòng thử lại.")
            return []

class ActionHandbookSearch(Action):
    """Action để tìm kiếm thông tin cụ thể trong sổ tay"""
    
    def __init__(self):
        super().__init__()
        self.chatbot = None
        self._load_chatbot()
    
    def _load_chatbot(self):
        """Tải chatbot handbook"""
        try:
            self.chatbot = HandbookChatbot()
            self.chatbot.load_model()
            
            if not self.chatbot.load_index():
                chunks = self.chatbot.parse_handbook("handbook_summary.txt")
                self.chatbot.create_embeddings(chunks)
                self.chatbot.save_index()
            
            logger.info("Handbook chatbot đã được tải thành công!")
        except Exception as e:
            logger.error(f"Lỗi khi tải handbook chatbot: {e}")
            self.chatbot = None
    
    def name(self) -> str:
        return "action_handbook_search"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list:
        """Tìm kiếm thông tin cụ thể"""
        
        if self.chatbot is None:
            dispatcher.utter_message(text="Xin lỗi, hệ thống handbook đang gặp sự cố.")
            return []
        
        # Lấy từ khóa tìm kiếm
        search_term = tracker.get_slot("search_term")
        user_message = tracker.latest_message.get('text', '')
        
        if not search_term and not user_message:
            dispatcher.utter_message(text="Vui lòng cung cấp từ khóa để tìm kiếm.")
            return []
        
        # Sử dụng search_term nếu có, không thì dùng user_message
        query = search_term if search_term else user_message
        
        try:
            # Tìm kiếm với nhiều kết quả hơn
            results = self.chatbot.search(query, top_k=5)
            
            if not results:
                dispatcher.utter_message(text=f"Không tìm thấy thông tin về '{query}' trong sổ tay sinh viên.")
                return []
            
            # Tạo câu trả lời chi tiết
            answer_parts = [f"Kết quả tìm kiếm cho '{query}':\n"]
            
            for i, result in enumerate(results[:3], 1):  # Chỉ hiển thị 3 kết quả đầu
                chunk = result['chunk']
                score = result['score']
                
                if score > 0.2:  # Ngưỡng thấp hơn cho tìm kiếm
                    answer_parts.append(f"{i}. **{chunk['title']}** (Độ tin cậy: {score:.2f})")
                    answer_parts.append(f"   {chunk['content'][:200]}...")
                    answer_parts.append("")
            
            answer = "\n".join(answer_parts)
            dispatcher.utter_message(text=answer)
            
            return [SlotSet("search_term", None)]
            
        except Exception as e:
            logger.error(f"Lỗi khi tìm kiếm handbook: {e}")
            dispatcher.utter_message(text="Xin lỗi, có lỗi xảy ra khi tìm kiếm.")
            return []

class ActionHandbookTopics(Action):
    """Action để liệt kê các chủ đề có trong sổ tay"""
    
    def __init__(self):
        super().__init__()
        self.chatbot = None
        self._load_chatbot()
    
    def _load_chatbot(self):
        """Tải chatbot handbook"""
        try:
            self.chatbot = HandbookChatbot()
            self.chatbot.load_model()
            
            if not self.chatbot.load_index():
                chunks = self.chatbot.parse_handbook("handbook_summary.txt")
                self.chatbot.create_embeddings(chunks)
                self.chatbot.save_index()
            
            logger.info("Handbook chatbot đã được tải thành công!")
        except Exception as e:
            logger.error(f"Lỗi khi tải handbook chatbot: {e}")
            self.chatbot = None
    
    def name(self) -> str:
        return "action_handbook_topics"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list:
        """Liệt kê các chủ đề trong sổ tay"""
        
        if self.chatbot is None:
            dispatcher.utter_message(text="Xin lỗi, hệ thống handbook đang gặp sự cố.")
            return []
        
        try:
            topics = []
            for chunk in self.chatbot.chunks:
                if chunk['title']:
                    topics.append(chunk['title'])
            
            if topics:
                answer = "**Các chủ đề chính trong Sổ tay Sinh viên PTIT:**\n\n"
                for i, topic in enumerate(topics[:10], 1):  # Chỉ hiển thị 10 chủ đề đầu
                    answer += f"{i}. {topic}\n"
                
                if len(topics) > 10:
                    answer += f"\n... và {len(topics) - 10} chủ đề khác."
                
                dispatcher.utter_message(text=answer)
            else:
                dispatcher.utter_message(text="Không thể tải danh sách chủ đề.")
                
        except Exception as e:
            logger.error(f"Lỗi khi liệt kê chủ đề: {e}")
            dispatcher.utter_message(text="Xin lỗi, có lỗi xảy ra khi tải danh sách chủ đề.")
        
        return [] 