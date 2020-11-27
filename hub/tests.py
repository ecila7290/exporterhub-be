import json

from django.test import TestCase, Client

from .models import Category

client=Client()

class CategoryTest(TestCase):
    def setUp(self):
        Category.objects.create(
            id=1,
            name='category1'
        )
    
    def tearDown(self):
        Category.objects.all().delete()

    def test_get_category_success(self):
        response=client.get('/categories')
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json(),
            {
                'categories':[{
                'category_id':1,
                'category_name':'category1'}]
            }
        )

    def test_get_category_not_found(self):
        response=client.get('/category')
        self.assertEqual(response.status_code,404)