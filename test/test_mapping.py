"""카테고리 매핑 테스트"""
from unified_mapper import UnifiedCategoryMapper
import logging

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

def test_category_mapping():
    mapper = UnifiedCategoryMapper()
    
    while True:
        print("\n=== 카테고리 매핑 테스트 ===")
        print("1. arXiv")
        print("2. bioRxiv/medRxiv") 
        print("3. PMC")
        print("4. PLOS")
        print("5. DOAJ")
        print("6. CORE")
        print("7. 전체 Level1 카테고리 보기")
        print("8. Level1별 검색")
        print("0. 종료")
        
        choice = input("선택: ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            test_platform_mapping(mapper, 'arxiv')
        elif choice == '2':
            test_platform_mapping(mapper, 'biorxiv')
        elif choice == '3':
            test_platform_mapping(mapper, 'pmc')
        elif choice == '4':
            test_platform_mapping(mapper, 'plos')
        elif choice == '5':
            test_platform_mapping(mapper, 'doaj')
        elif choice == '6':
            test_platform_mapping(mapper, 'core')
        elif choice == '7':
            show_all_level1(mapper)
        elif choice == '8':
            search_by_level1(mapper)
        else:
            print("잘못된 선택")

def test_platform_mapping(mapper, platform):
    print(f"\n=== {platform.upper()} 카테고리 매핑 테스트 ===")
    
    categories = mapper.get_platform_categories(platform)
    if not categories:
        print(f"{platform} 카테고리가 없습니다")
        return
        
    print(f"사용 가능한 카테고리 ({len(categories)}개):")
    for orig_cat in sorted(categories.keys()):
        print(f"  - {orig_cat}")
    
    while True:
        category = input(f"\n테스트할 {platform} 카테고리 (빈 값으로 돌아가기): ").strip()
        if not category:
            break
            
        try:
            result = mapper.normalize_category(platform, category)
            print(f"\n매핑 결과:")
            print(f"  원본: {result['original']}")
            print(f"  플랫폼: {result['platform']}")
            print(f"  Level1: {result['level1']}")
            print(f"  Level2: {result['level2']}")
            logger.error(f"TEST: {platform}.{category} -> {result}")
        except Exception as e:
            print(f"오류: {e}")
            logger.error(f"TEST_ERROR: {platform}.{category} failed: {e}")

def show_all_level1(mapper):
    print("\n=== 전체 Level1 카테고리 ===")
    categories = mapper.get_all_level1_categories()
    for i, cat in enumerate(categories, 1):
        print(f"{i:2d}. {cat}")
    logger.error(f"SHOW_ALL_LEVEL1: {len(categories)} categories displayed")

def search_by_level1(mapper):
    print("\n=== Level1별 검색 ===")
    level1 = input("검색할 Level1 카테고리: ").strip()
    if not level1:
        return
        
    results = mapper.search_by_level1(level1)
    if not results:
        print(f"'{level1}' 카테고리를 찾을 수 없습니다")
        return
        
    print(f"\n'{level1}' 카테고리 검색 결과:")
    for platform, categories in results.items():
        print(f"\n[{platform.upper()}] ({len(categories)}개)")
        for cat_data in categories:
            print(f"  {cat_data['original']} -> {cat_data['level2']}")
    
    logger.error(f"SEARCH_LEVEL1: '{level1}' found in {len(results)} platforms")

if __name__ == "__main__":
    test_category_mapping()
