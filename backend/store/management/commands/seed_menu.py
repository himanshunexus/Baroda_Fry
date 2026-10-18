import os
from django.core.management.base import BaseCommand
from store.models import Dish
DATA = [
('Chicken Tikka','Starters',22000,'6 Pcs','Smoky, charred chicken with our signature spice marinade.','photo-1599487488170-d11ec9c172f0',True),
('Butter Chicken','Chicken',26000,'Full','Tender chicken in a rich, creamy tomato gravy.','photo-1603894584373-5ac82b2ae398',True),
('Chicken Dum Biryani','Rice & Biryani',20000,'Full','Fragrant basmati, slow-cooked chicken and warming spices.','photo-1589302168068-964664d93dc0',True),
('Mutton Rogan Josh','Mutton',34000,'Full','Slow-cooked mutton in an aromatic, deeply spiced gravy.','photo-1545247181-516773cae754',False),
('Chicken Seekh Kebab','Starters',18000,'4 Pcs','Juicy minced chicken, fresh herbs and a kiss of charcoal.','photo-1601050690597-df0568f70950',False),
('Chicken Masala','Chicken',24000,'Full','Our homestyle chicken curry with a bold masala finish.','photo-1631452180519-c014fe946bc7',False),
('Mutton Dum Biryani','Rice & Biryani',30000,'Full','Tender mutton layered with saffron-scented basmati rice.','photo-1642821373181-696a54913e93',True),
('Butter Naan','Breads',4500,'1 Pc','Soft tandoor-baked bread brushed with melted butter.','photo-1633436374961-09b92742047b',False),
('Chicken Tikka','Starters',12000,'3 Pcs','A smaller serving of our smoky, charred chicken favourite.','photo-1599487488170-d11ec9c172f0',False),
('Jeera Rice','Rice & Biryani',10000,'Full','Fluffy basmati rice tempered with toasted cumin.','photo-1516684732162-798a0062be99',False),
('Fresh Lime Soda','Extras',6000,'300 ml','A refreshing squeeze of lime with a sparkling finish.','photo-1544145945-f90425340c7e',False),
('Boondi Raita','Extras',5000,'150 ml','Cool, creamy yoghurt with crisp boondi and roasted cumin.','photo-1488477181946-6428a0291777',False),
]
class Command(BaseCommand):
    help = 'Seed illustrative menu and sample prices. --cloudinary uploads Unsplash images to your account.'
    def add_arguments(self, parser): parser.add_argument('--cloudinary', action='store_true')
    def handle(self, *args, **options):
        for name,cat,price,portion,desc,photo,best in DATA:
            url=f'https://images.unsplash.com/{photo}?auto=format&fit=crop&w=700&q=85'
            if options['cloudinary']:
                if not os.getenv('CLOUDINARY_URL'): raise RuntimeError('Set CLOUDINARY_URL first')
                import cloudinary.uploader
                url=cloudinary.uploader.upload(url, folder='baroda-fry-centre', public_id=photo, overwrite=False)['secure_url']
            Dish.objects.update_or_create(name=name, portion_label=portion, defaults=dict(category=cat,price_paise=price,description=desc,image_cloudinary_url=url,spice_choices_supported=['Mild','Medium','Hot'] if cat not in ['Breads','Extras'] else [],is_bestseller=best))
        self.stdout.write(self.style.SUCCESS('Seeded 12 dishes with sample prices; verify before launch.'))
