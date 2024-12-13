from rest_framework.decorators import api_view
from rest_framework.response import Response
from price_scraper.tasks.user_triggered_scrape import user_triggered_scrape 
from price_scraper.tasks.testing import testing_req
import json

@api_view(['GET'])
def trigger_scraping(request):
    """
    View to trigger user scraping.
    """
    product_data = {
        "product_name": request.GET.get('product_name'),
        "amazon_url": request.GET.get('amazon_url'),
        "flipkart_url": request.GET.get('flipkart_url'),
        "callback_url": request.GET.get('callback_url')
    }

    if not product_data['product_name'] or not product_data['amazon_url'] or not product_data['flipkart_url'] or not product_data['callback_url']:
        return Response({"message": "Please provide all required fields."})
    
    # Trigger user-triggered scraping task
    try:
        task = user_triggered_scrape.delay(product_data)
        task_id = task.id
    except Exception as e:
        return Response({"message": f"Error triggering scraping: {str(e)}"})
    
    # Poll the task result
    task_result = task.get(timeout=30)  # Set a timeout for waiting for the result

    if task_result == 'success':
        return Response({"message": "Scraping triggered successfully.", "task_id": task_id, "status": "success"})
    else:
        return Response({"message": "Scraping failed.", "task_id": task_id, "status": "failed"})

@api_view(['GET'])
def main(request):
    return Response({"message": "Hello, world!"})
