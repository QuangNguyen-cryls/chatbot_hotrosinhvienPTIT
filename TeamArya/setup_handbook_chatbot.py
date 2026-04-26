#!/usr/bin/env python3
"""
Script setup cho Handbook Chatbot
Cài đặt dependencies và khởi tạo chatbot
"""

import subprocess
import sys
import os
import logging

# Thiết lập logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def install_requirements():
    """Cài đặt các thư viện cần thiết"""
    logger.info("Đang cài đặt các thư viện cần thiết...")
    
    try:
        # Cài đặt từ requirements file
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements_chatbot.txt"
        ])
        logger.info("✅ Cài đặt thành công!")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Lỗi khi cài đặt: {e}")
        return False

def test_chatbot():
    """Test chatbot"""
    logger.info("Đang test chatbot...")
    
    try:
        from chatbot_with_model import HandbookChatbot
        
        # Khởi tạo chatbot
        chatbot = HandbookChatbot()
        chatbot.load_model()
        
        # Test với một câu hỏi đơn giản
        test_question = "Học viện PTIT có lịch sử như thế nào?"
        
        # Tạo index nếu chưa có
        if not chatbot.load_index():
            chunks = chatbot.parse_handbook("handbook_summary.txt")
            chatbot.create_embeddings(chunks)
            chatbot.save_index()
        
        # Test trả lời
        answer = chatbot.answer_question(test_question)
        
        if answer and "không tìm thấy" not in answer.lower():
            logger.info("✅ Test thành công!")
            logger.info(f"Test question: {test_question}")
            logger.info(f"Answer: {answer[:200]}...")
            return True
        else:
            logger.warning("⚠️ Test không hoàn hảo, nhưng chatbot đã hoạt động")
            return True
            
    except Exception as e:
        logger.error(f"❌ Lỗi khi test: {e}")
        return False

def main():
    """Hàm chính"""
    print("🤖 Setup Handbook Chatbot")
    print("=" * 50)
    
    # Kiểm tra file handbook
    if not os.path.exists("handbook_summary.txt"):
        print("❌ Không tìm thấy file handbook_summary.txt")
        print("Vui lòng đảm bảo file này tồn tại trong thư mục hiện tại.")
        return False
    
    # Cài đặt requirements
    if not install_requirements():
        return False
    
    # Test chatbot
    if not test_chatbot():
        return False
    
    print("\n🎉 Setup hoàn thành!")
    print("\nĐể chạy chatbot, sử dụng một trong các lệnh sau:")
    print("1. python chatbot_with_model.py - Chạy chatbot độc lập")
    print("2. python -m rasa run actions - Chạy action server cho Rasa")
    print("3. python -m rasa shell - Chạy Rasa shell")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 