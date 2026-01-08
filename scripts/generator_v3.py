import os
import time
import google.generativeai as genai
from slugify import slugify

# Если файла topics.py нет, используем встроенный тестовый список
try:
    from topics import topics
except ImportError:
    topics = [
        "Тестовая тема 1: Будущее VPN",
        "Тестовая тема 2: Настройка VLESS"
    ]

# --- ВСТАВЬТЕ СЮДА ВАШ КЛЮЧ ---
GOOGLE_API_KEY = "AIzaSyDgYOAYZzz97fdbOiG7Ew00eoDjInrqcak"  # <--- ВЕРНУЛ ВАШ КЛЮЧ

# --- ЖЕЛАЕМАЯ МОДЕЛЬ ---
TARGET_MODEL_NAME = "gemini-3-flash"

# --- НАСТРОЙКА ---
genai.configure(api_key=GOOGLE_API_KEY)
BASE_OUTPUT_DIR = "../src/content/blog" 

def get_working_model():
    """
    Ищет модель. Приоритет: gemini-3-flash -> gemini-2.0-flash -> gemini-1.5-flash
    """
    print("🔍 Сканирую доступные модели в API Google...")
    
    available_models = []
    try:
        # Получаем список всех доступных вам моделей
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
    except Exception as e:
        print(f"❌ Ошибка соединения с API: {e}")
        return None

    # 1. Пробуем найти именно ту, которую вы просили (gemini-3-flash)
    for model_name in available_models:
        if TARGET_MODEL_NAME in model_name:
            print(f"✅ УРА! Найдена модель: {model_name}")
            return genai.GenerativeModel(model_name)

    # 2. Если 3-й версии нет, ищем 2.0 (экспериментальную) или 1.5
    print(f"⚠️ Модель '{TARGET_MODEL_NAME}' пока недоступна в API.")
    print("🔄 Переключаюсь на лучшую доступную альтернативу...")

    # Ищем любую Flash модель (они самые быстрые)
    for model_name in available_models:
        if "flash" in model_name and "gemini" in model_name:
            print(f"✅ Выбрана альтернатива: {model_name}")
            return genai.GenerativeModel(model_name)
            
    # Ищем любую Pro модель
    for model_name in available_models:
        if "pro" in model_name and "gemini" in model_name:
            print(f"✅ Выбрана альтернатива: {model_name}")
            return genai.GenerativeModel(model_name)

    print("❌ Не найдено ни одной модели Gemini.")
    return None

def get_system_prompt(topic):
    if "2026" in topic:
        return """
        Ты — IT-журналист из будущего (середина 2026 года). 
        Твоя задача — написать обзор VPN сервисов в условиях тотальной изоляции рунета.
        Легенда мира 2026: Работают только VLESS, Reality и спутниковый интернет. 
        Придумай вымышленные названия сервисов. Дата публикации: 2026-02-20.
        """
    return "Ты — эксперт по кибербезопасности. Пиши статью в формате Markdown для блога."

def generate_content(model, topic):
    folder = "general"
    if any(x in topic.lower() for x in ["рейтинг", "топ", "обзор"]):
        folder = "reviews"
    elif any(x in topic.lower() for x in ["как", "гайд", "настройка", "инструкция"]):
        folder = "guides"
    
    # Проверка на существование файла
    filename = slugify(topic) + ".md"
    target_path = os.path.join(BASE_OUTPUT_DIR, folder, filename)
    if os.path.exists(target_path):
        print(f"⏭️ Пропуск (файл уже существует): {topic}")
        return None, None
        
    print(f"🚀 Генерирую: {topic} -> папка /{folder}...")

    prompt = f"""
    {get_system_prompt(topic)}
    
    ТВОЯ ЗАДАЧА: Напиши статью на тему "{topic}".
    
    ТРЕБОВАНИЯ:
    1. Frontmatter в начале (ОБЯЗАТЕЛЬНО):
    ---
    title: '{topic}'
    description: 'SEO описание до 160 символов'
    pubDate: 2026-02-20
    author: 'NetFreedom Admin'
    image: '/images/{slugify(topic)}.jpg'
    tags: ['VPN', 'Security']
    ---
    
    2. Используй чистый Markdown. НЕ пиши ```markdown в начале и конце.
    3. Объем: от 4000 знаков.
    """

    try:
        response = model.generate_content(prompt)
        text = response.text
        # Очистка от лишних символов, если нейросеть их добавила
        text = text.replace("```markdown", "").replace("```", "").strip()
        return text, folder
    except Exception as e:
        print(f"❌ Ошибка генерации: {e}")
        return None, None

def save_file(topic, content, folder):
    target_dir = os.path.join(BASE_OUTPUT_DIR, folder)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    filename = slugify(topic) + ".md"
    filepath = os.path.join(target_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Сохранено: {filepath}")

# --- ЗАПУСК ---
if __name__ == "__main__":
    model = get_working_model()
    
    if model:
        print(f"🎯 Всего тем в очереди: {len(topics)}")
        for i, topic in enumerate(topics):
            content, folder = generate_content(model, topic)
            if content:
                save_file(topic, content, folder)
                # Gemini имеет лимиты (RPM). 4 секунды паузы — безопасно для Free tier.
                time.sleep(4) 
            else:
                pass 
    else:
        print("Скрипт остановлен из-за ошибки доступа к моделям.")
