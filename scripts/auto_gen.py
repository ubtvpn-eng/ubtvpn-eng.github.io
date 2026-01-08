import os
import time
import google.generativeai as genai
from slugify import slugify

# --- ВСТАВЬТЕ СЮДА ВАШ КЛЮЧ ---
GOOGLE_API_KEY = "AIzaSyDgYOAYZzz97fdbOiG7Ew00eoDjInrqcak" 

# --- ТЕМЫ ---
TOPICS = [
    "Рейтинг VPN России 2026: Кто выжил после Чебурнета",
    "Топ-5 сервисов для обхода блокировок: Обзор 2026",
    "Как настроить VLESS на роутере Keenetic: Гайд",
    "Настройка AmneziaWG для чайников: Инструкция",
    "Почему интернет стал таким медленным: Анализ",
]

# --- НАСТРОЙКА ---
genai.configure(api_key=GOOGLE_API_KEY)
BASE_OUTPUT_DIR = "../src/content/blog" # Corrected path to point to parent src

def get_working_model():
    """Функция сама ищет доступную модель Gemini"""
    print("🔍 Ищу доступные модели...")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'gemini' in m.name:
                    print(f"✅ Найдена рабочая модель: {m.name}")
                    return genai.GenerativeModel(m.name)
    except Exception as e:
        print(f"❌ Ошибка при поиске моделей: {e}")
        return None
    
    print("❌ Не найдено ни одной модели Gemini. Проверьте API ключ.")
    return None

def get_system_prompt(topic):
    if "2026" in topic:
        return """
        Ты — IT-журналист из будущего (середина 2026 года). 
        Твоя задача — написать обзор VPN сервисов в условиях тотальной изоляции рунета.
        Легенда мира 2026: Работают только VLESS, Reality и спутниковый интернет. 
        Придумай вымышленные названия сервисов. Дата: 2026-02-20.
        """
    return "Ты — эксперт по кибербезопасности. Пиши статью в формате Markdown для блога."

def generate_content(model, topic):
    folder = "general"
    if any(x in topic.lower() for x in ["рейтинг", "топ", "обзор"]):
        folder = "reviews"
    elif any(x in topic.lower() for x in ["как", "гайд", "настройка", "инструкция"]):
        folder = "guides"
        
    print(f"🚀 Генерирую: {topic} -> папка /{folder}...")

    prompt = f"""
    {get_system_prompt(topic)}
    
    ТВОЯ ЗАДАЧА: Напиши статью на тему "{topic}".
    
    ТРЕБОВАНИЯ:
    1. Frontmatter в начале (ОБЯЗАТЕЛЬНО):
    ---
    title: '{topic}'
    description: 'SEO описание'
    pubDate: 2026-02-20
    author: 'NetFreedom Admin'
    image: '/images/{slugify(topic)}.jpg'
    tags: ['VPN', 'Security']
    ---
    
    2. Используй Markdown (H2, H3, code blocks).
    3. Объем: от 3000 знаков.
    """

    try:
        response = model.generate_content(prompt)
        return response.text, folder
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
        for topic in TOPICS:
            content, folder = generate_content(model, topic)
            if content:
                save_file(topic, content, folder)
                time.sleep(4) # Пауза важна для бесплатного тарифа
    else:
        print("Скрипт остановлен из-за ошибки доступа к моделям.")
