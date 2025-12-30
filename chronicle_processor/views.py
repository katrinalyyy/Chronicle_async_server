"""
Views для асинхронной обработки заявок на исследование хроник.
"""
import time
import random
import requests
from concurrent.futures import ThreadPoolExecutor
from django.conf import settings
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework import status
import json


# Пул потоков для выполнения асинхронных задач
executor = ThreadPoolExecutor(max_workers=10)


def calculate_chronicle_accuracy(chronicle_research_id, quote, chronicle_text):
    """
    Вычисляет точность анализа цитаты (accuracy) на основе сравнения с текстом хроники.
    
    Args:
        chronicle_research_id: ID записи м-м связи
        quote: Цитата из хроники
        chronicle_text: Полный текст хроники (опционально, для реального анализа)
    
    Returns:
        float: Точность анализа от 0.0 до 1.0
    """
    # Имитация вычисления точности с задержкой 5-10 секунд
    delay = random.uniform(5.0, 10.0)
    time.sleep(delay)
    
    # Простая логика: если цитата не пустая, генерируем случайную точность
    # В реальной системе здесь был бы анализ текста, сравнение с оригиналом и т.д.
    if quote and len(quote.strip()) > 0:
        # Генерируем точность от 0.7 до 1.0 для непустых цитат
        accuracy = random.uniform(0.7, 1.0)
    else:
        # Для пустых цитат точность низкая
        accuracy = random.uniform(0.0, 0.3)
    
    return accuracy


def send_results_to_main_service(request_id, results):
    """
    Отправляет результаты обработки в основной сервис.
    
    Args:
        request_id: ID заявки
        results: Список словарей с результатами обработки каждой хроники
                 [{"chronicle_research_id": 1, "accuracy": 0.95}, ...]
    """
    try:
        url = f"{settings.MAIN_SERVICE_URL}/api/ChronicleRequestList/{request_id}/update-results"
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': settings.API_KEY,
        }
        payload = {
            'results': results
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        print(f"✓ Результаты успешно отправлены в основной сервис для заявки {request_id}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"✗ Ошибка при отправке результатов в основной сервис: {e}")
        return False


def process_chronicle_research_async(request_id, chronicles_data):
    """
    Асинхронная обработка заявки: вычисление точности для каждой хроники.
    
    Args:
        request_id: ID заявки
        chronicles_data: Список словарей с данными хроник
                        [{"id": 1, "quote": "...", "chronicle_text": "..."}, ...]
    """
    print(f"Начата обработка заявки {request_id} с {len(chronicles_data)} хрониками")
    
    results = []
    
    # Обрабатываем каждую хронику
    for chronicle in chronicles_data:
        chronicle_research_id = chronicle.get('id')
        quote = chronicle.get('quote', '')
        chronicle_text = chronicle.get('chronicle_text', '')
        
        # Вычисляем точность
        accuracy = calculate_chronicle_accuracy(chronicle_research_id, quote, chronicle_text)
        
        results.append({
            'chronicle_research_id': chronicle_research_id,
            'accuracy': round(accuracy, 4),  # Округляем до 4 знаков
        })
        
        print(f"  Обработана хроника {chronicle_research_id}: accuracy = {accuracy:.4f}")
    
    # Отправляем результаты в основной сервис
    success = send_results_to_main_service(request_id, results)
    
    if success:
        print(f"✓ Заявка {request_id} успешно обработана")
    else:
        print(f"✗ Ошибка при обработке заявки {request_id}")


@api_view(['POST'])
def process_chronicle_research(request):
    """
    Эндпоинт для запуска асинхронной обработки заявки.
    
    Принимает:
    {
        "request_id": 1,
        "chronicles": [
            {"id": 1, "quote": "...", "chronicle_text": "..."},
            ...
        ]
    }
    
    Возвращает сразу 200 OK, обработка выполняется в фоне.
    """
    try:
        data = json.loads(request.body)
        request_id = data.get('request_id')
        chronicles = data.get('chronicles', [])
        
        if not request_id:
            return JsonResponse(
                {'error': 'request_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not chronicles:
            return JsonResponse(
                {'error': 'chronicles list is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Запускаем асинхронную обработку в отдельном потоке
        executor.submit(process_chronicle_research_async, request_id, chronicles)
        
        return JsonResponse({
            'status': 'success',
            'message': f'Processing started for request {request_id}',
            'request_id': request_id,
            'chronicles_count': len(chronicles)
        }, status=status.HTTP_200_OK)
        
    except json.JSONDecodeError:
        return JsonResponse(
            {'error': 'Invalid JSON'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return JsonResponse(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

