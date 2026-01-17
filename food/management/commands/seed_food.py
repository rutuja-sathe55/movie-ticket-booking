from django.core.management.base import BaseCommand
from django.db import transaction
from food.models import FoodCategory, FoodItem
from decimal import Decimal


class Command(BaseCommand):
    help = 'Seed food items: 10 items per category (Popcorn, Drinks, Snacks, Combos, Desserts)'

    def handle(self, *args, **options):
        with transaction.atomic():
            # Define food categories and items
            categories_data = {
                'Popcorn': [
                    {'name': 'Small Popcorn', 'price': Decimal('150'), 'veg': True, 'desc': 'Classic buttered popcorn'},
                    {'name': 'Medium Popcorn', 'price': Decimal('200'), 'veg': True, 'desc': 'Medium buttered popcorn'},
                    {'name': 'Large Popcorn', 'price': Decimal('250'), 'veg': True, 'desc': 'Large buttered popcorn'},
                    {'name': 'Cheese Popcorn', 'price': Decimal('220'), 'veg': True, 'desc': 'Popcorn with cheese flavour'},
                    {'name': 'Caramel Popcorn', 'price': Decimal('230'), 'veg': True, 'desc': 'Sweet caramel flavoured popcorn'},
                    {'name': 'Spicy Popcorn', 'price': Decimal('210'), 'veg': True, 'desc': 'Hot and spicy popcorn'},
                    {'name': 'Butter Garlic Popcorn', 'price': Decimal('240'), 'veg': True, 'desc': 'Butter and garlic flavoured'},
                    {'name': 'Chocolate Popcorn', 'price': Decimal('260'), 'veg': True, 'desc': 'Chocolate coated popcorn', 'dairy': True},
                    {'name': 'Honey Popcorn', 'price': Decimal('250'), 'veg': True, 'desc': 'Sweet honey drizzled popcorn'},
                    {'name': 'Premium Mix Popcorn', 'price': Decimal('280'), 'veg': True, 'desc': 'Premium mix with all flavours'},
                ],
                'Drinks': [
                    {'name': 'Coca Cola', 'price': Decimal('100'), 'veg': True, 'desc': 'Cold Coca Cola'},
                    {'name': 'Pepsi', 'price': Decimal('100'), 'veg': True, 'desc': 'Cold Pepsi'},
                    {'name': 'Sprite', 'price': Decimal('100'), 'veg': True, 'desc': 'Refreshing Sprite'},
                    {'name': 'Fanta Orange', 'price': Decimal('100'), 'veg': True, 'desc': 'Fanta Orange'},
                    {'name': 'Iced Tea', 'price': Decimal('80'), 'veg': True, 'desc': 'Cold iced tea'},
                    {'name': 'Coffee', 'price': Decimal('120'), 'veg': True, 'desc': 'Hot cappuccino coffee', 'dairy': True},
                    {'name': 'Hot Chocolate', 'price': Decimal('130'), 'veg': True, 'desc': 'Hot chocolate with milk', 'dairy': True},
                    {'name': 'Mineral Water', 'price': Decimal('50'), 'veg': True, 'desc': 'Chilled mineral water'},
                    {'name': 'Energy Drink', 'price': Decimal('110'), 'veg': True, 'desc': 'Refreshing energy drink'},
                    {'name': 'Milkshake', 'price': Decimal('140'), 'veg': True, 'desc': 'Creamy vanilla milkshake', 'dairy': True},
                ],
                'Snacks': [
                    {'name': 'Nachos', 'price': Decimal('180'), 'veg': True, 'desc': 'Crispy nachos with cheese'},
                    {'name': 'Samosa', 'price': Decimal('80'), 'veg': True, 'desc': 'Traditional Indian samosa'},
                    {'name': 'Paneer Fries', 'price': Decimal('150'), 'veg': True, 'desc': 'Crispy paneer fries', 'dairy': True},
                    {'name': 'Spring Rolls', 'price': Decimal('120'), 'veg': True, 'desc': 'Vegetable spring rolls'},
                    {'name': 'Momos', 'price': Decimal('100'), 'veg': True, 'desc': 'Steamed vegetable momos'},
                    {'name': 'Fries', 'price': Decimal('120'), 'veg': True, 'desc': 'Golden crispy fries'},
                    {'name': 'Chikhalwali', 'price': Decimal('140'), 'veg': True, 'desc': 'Fried chikhalwali snack'},
                    {'name': 'Bhel Puri', 'price': Decimal('100'), 'veg': True, 'desc': 'Traditional bhel puri'},
                    {'name': 'Cheese Loaded Nachos', 'price': Decimal('220'), 'veg': True, 'desc': 'Nachos loaded with melted cheese', 'dairy': True},
                    {'name': 'Corn Cheese Balls', 'price': Decimal('160'), 'veg': True, 'desc': 'Cheesy corn snack balls', 'dairy': True},
                ],
                'Combos': [
                    {'name': 'Popcorn + Drink Combo', 'price': Decimal('250'), 'veg': True, 'desc': 'Popcorn with any drink'},
                    {'name': 'Movie Lover Combo', 'price': Decimal('350'), 'veg': True, 'desc': 'Popcorn + Snack + Drink'},
                    {'name': 'Family Pack Combo', 'price': Decimal('500'), 'veg': True, 'desc': 'Large popcorn x2 + 2 drinks'},
                    {'name': 'Premium Combo', 'price': Decimal('450'), 'veg': True, 'desc': 'Premium items bundled'},
                    {'name': 'Midnight Snacker Combo', 'price': Decimal('300'), 'veg': True, 'desc': 'Snacks + Drink combo'},
                    {'name': 'Quick Bite Combo', 'price': Decimal('200'), 'veg': True, 'desc': 'Light snack + drink'},
                    {'name': 'Sweet Treat Combo', 'price': Decimal('280'), 'veg': True, 'desc': 'Dessert + Hot beverage', 'dairy': True},
                    {'name': 'Spicy Lover Combo', 'price': Decimal('320'), 'veg': True, 'desc': 'Spicy snacks bundle'},
                    {'name': 'Party Combo', 'price': Decimal('600'), 'veg': True, 'desc': 'Large combo for 4 people'},
                    {'name': 'Value Pack Combo', 'price': Decimal('199'), 'veg': True, 'desc': 'Best value combo'},
                ],
                'Desserts': [
                    {'name': 'Chocolate Brownie', 'price': Decimal('180'), 'veg': True, 'desc': 'Rich chocolate brownie', 'dairy': True},
                    {'name': 'Ice Cream Cup', 'price': Decimal('120'), 'veg': True, 'desc': 'Vanilla ice cream', 'dairy': True},
                    {'name': 'Donut', 'price': Decimal('100'), 'veg': True, 'desc': 'Glazed donut', 'gluten': True, 'dairy': True},
                    {'name': 'Cheesecake Slice', 'price': Decimal('200'), 'veg': True, 'desc': 'Creamy cheesecake', 'dairy': True},
                    {'name': 'Candy Box', 'price': Decimal('150'), 'veg': True, 'desc': 'Assorted candies'},
                    {'name': 'Chocolate Chip Cookie', 'price': Decimal('80'), 'veg': True, 'desc': 'Soft chocolate chip cookie', 'gluten': True, 'dairy': True},
                    {'name': 'Waffle', 'price': Decimal('140'), 'veg': True, 'desc': 'Hot waffle with syrup', 'gluten': True, 'dairy': True},
                    {'name': 'Pastry', 'price': Decimal('110'), 'veg': True, 'desc': 'Buttery pastry', 'gluten': True, 'dairy': True},
                    {'name': 'Fruit Smoothie', 'price': Decimal('130'), 'veg': True, 'desc': 'Fresh fruit smoothie'},
                    {'name': 'Dessert Platter', 'price': Decimal('300'), 'veg': True, 'desc': 'Mixed desserts platter', 'dairy': True, 'gluten': True},
                ],
            }
            
            created_count = 0
            for cat_name, items in categories_data.items():
                category, cat_created = FoodCategory.objects.get_or_create(name=cat_name)
                if cat_created:
                    self.stdout.write(self.style.SUCCESS(f"✓ Created category: {cat_name}"))
                
                for item_data in items:
                    name = item_data['name']
                    price = item_data['price']
                    veg = item_data.get('veg', False)
                    desc = item_data.get('desc', f'{name} at {cat_name}')
                    dairy = item_data.get('dairy', False)
                    gluten = item_data.get('gluten', False)
                    
                    food_item, created = FoodItem.objects.get_or_create(
                        name=name,
                        category=category,
                        defaults={
                            'description': desc,
                            'price': price,
                            'quantity_unit': 'piece',
                            'available_quantity': 100,
                            'is_available': True,
                            'is_vegetarian': veg,
                            'contains_dairy': dairy,
                            'contains_gluten': gluten,
                        }
                    )
                    if created:
                        created_count += 1
                        self.stdout.write(self.style.SUCCESS(f"  ✓ {name} - ₹{price}"))
            
            self.stdout.write(self.style.SUCCESS(f'\n✓ Food seeding complete: {created_count} items across {len(categories_data)} categories'))
