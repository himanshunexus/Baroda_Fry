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
('Chicken Tikka','Starters',12000,'3 Pcs','A smaller serving of our smoky, charred chicken favourite.','photo-1610057099431-d73a1c9d2f2f',False),
('Jeera Rice','Rice & Biryani',10000,'Full','Fluffy basmati rice tempered with toasted cumin.','photo-1789991184293-224a84e41900',False),
('Fresh Lime Soda','Extras',6000,'300 ml','A refreshing squeeze of lime with a sparkling finish.','photo-1544145945-f90425340c7e',False),
('Boondi Raita','Extras',5000,'150 ml','Cool, creamy yoghurt with crisp boondi and roasted cumin.','photo-1488477181946-6428a0291777',False),
('Tandoori Chicken','Starters',28000,'Half','Chicken roasted with a smoky tandoori spice marinade.','photo-1605908580297-f3e1c02e64ff',False),
('Chicken Malai Tikka','Starters',24000,'6 Pcs','Tender chicken pieces in a mild, creamy marinade.','photo-1778449588437-97bd47f88276',False),
('Mutton Seekh Kebab','Starters',26000,'4 Pcs','Spiced minced mutton shaped into skewers and grilled.','photo-1781332143834-19a40f746cd9',False),
('Chicken 65','Starters',22000,'Full','Crisp, punchy chicken bites with a chilli-garlic finish.','photo-1727280376746-b89107a5b0df',False),
('Chicken Kadai','Chicken',27000,'Full','Chicken simmered with peppers and a warming kadai masala.','photo-1694579740719-0e601c5d2437',False),
('Chicken Korma','Chicken',28000,'Full','A gently spiced chicken curry with a rich, creamy sauce.','photo-1708782344490-9026aaa5eec7',False),
('Chicken Tikka Masala','Chicken',29000,'Full','Grilled chicken tikka folded into a tomato masala gravy.','photo-1742599361574-6fb156181466',False),
('Mutton Curry','Mutton',35000,'Full','Slow-cooked mutton in a robust homestyle curry.','photo-1596797038530-2c107229654b',False),
('Mutton Keema','Mutton',32000,'Full','Minced mutton cooked with onions, spices and fresh herbs.','photo-1652545297020-f5e8ad779eb4',False),
('Egg Biryani','Rice & Biryani',17000,'Full','Fragrant basmati layered with spiced eggs and fried onions.','photo-1563379091339-03b21ab4a4f8',False),
('Veg Pulao','Rice & Biryani',15000,'Full','Basmati rice tossed with vegetables and whole spices.','photo-1603133872878-684f208fb84b',False),
('Plain Rice','Rice & Biryani',8000,'Full','Steamed basmati rice, ready to pair with your favourite curry.','photo-1536304993881-ff6e9eefa2a6',False),
('Garlic Naan','Breads',6000,'1 Pc','Soft naan finished with garlic, coriander and butter.','photo-1756821752957-00bfcadc3748',False),
('Tandoori Roti','Breads',3000,'1 Pc','Whole-wheat flatbread baked in the tandoor.','photo-1640625314547-aee9a7696589',False),
('Laccha Paratha','Breads',5500,'1 Pc','Layered, flaky flatbread with a golden finish.','photo-1708783741187-ff1d081d87da',False),
('Cucumber Raita','Extras',5500,'150 ml','Cooling yoghurt with cucumber and a touch of cumin.','photo-1777199264017-84af9308a41f',False),
('Masala Chaas','Extras',5000,'300 ml','Chilled spiced buttermilk with coriander and roasted cumin.','photo-1759524323778-436094781e5b',False),
]
LEGACY_PHOTOS = {
    'photo-1599487488170-d11ec9c172f0', 'photo-1603894584373-5ac82b2ae398',
    'photo-1589302168068-964664d93dc0', 'photo-1545247181-516773cae754',
    'photo-1601050690597-df0568f70950', 'photo-1631452180519-c014fe946bc7',
    'photo-1642821373181-696a54913e93', 'photo-1633436374961-09b92742047b',
    'photo-1516684732162-798a0062be99', 'photo-1544145945-f90425340c7e',
    'photo-1488477181946-6428a0291777',
}
class Command(BaseCommand):
    help = 'Seed illustrative menu and sample prices. --cloudinary uploads Unsplash images to your account.'
    def add_arguments(self, parser): parser.add_argument('--cloudinary', action='store_true')
    def handle(self, *args, **options):
        created_count = updated_count = 0
        def image_url(photo):
            source=f'https://images.unsplash.com/{photo}?auto=format&fit=crop&w=700&q=85'
            if not options['cloudinary']:
                return source
            if not os.getenv('CLOUDINARY_URL'): raise RuntimeError('Set CLOUDINARY_URL first')
            try:
                import cloudinary.uploader
                return cloudinary.uploader.upload(source, folder='baroda-fry-centre', public_id=photo,
                                                   overwrite=False)['secure_url']
            except Exception:
                self.stderr.write(self.style.WARNING(f'Cloudinary upload failed for {photo}; using the source image.'))
                return source
        for name,cat,price,portion,desc,photo,best in DATA:
            dish = Dish.objects.filter(name=name, portion_label=portion).first()
            if dish:
                current = dish.image_cloudinary_url
                if photo in current and (not options['cloudinary'] or 'res.cloudinary.com/' in current):
                    continue
                if any(old in current for old in LEGACY_PHOTOS) or photo in current:
                    Dish.objects.filter(pk=dish.pk, image_cloudinary_url=current).update(image_cloudinary_url=image_url(photo))
                    updated_count += 1
                continue
            _, created = Dish.objects.get_or_create(name=name, portion_label=portion, defaults=dict(category=cat,price_paise=price,description=desc,image_cloudinary_url=image_url(photo),spice_choices_supported=['Mild','Medium','Hot'] if cat not in ['Breads','Extras'] else [],is_bestseller=best))
            created_count += created
        self.stdout.write(self.style.SUCCESS(f'Added {created_count} dishes, refreshed {updated_count} sample images ({len(DATA)} in catalog); verify prices before launch.'))
