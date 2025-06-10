"""카테고리 매핑 테스트"""
from unified_mapper import UnifiedCategoryMapper
import logging

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

def test_platform_mapping_direct(mapper, platform_name):
    print(f"\n=== {platform_name.upper()} 카테고리 매핑 테스트 (직접 실행) ===")
    categories = mapper.get_platform_categories(platform_name)
    if not categories:
        print(f"{platform_name} 카테고리가 없습니다")
        return False
        
    print(f"사용 가능한 카테고리 ({len(categories)}개):\n")
    # 몇 가지 예시 매핑 테스트
    test_categories = list(categories.keys())[:3] # 처음 3개 카테고리 테스트
    if not test_categories:
        print(f"테스트할 {platform_name} 카테고리가 충분하지 않습니다.")
        return False

    success = True
    for category in test_categories:
        try:
            result = mapper.normalize_category(platform_name, category)
            print(f"  ✅ {category} -> {result['level1']}.{result['level2']}")
            logger.error(f"TEST: {platform_name}.{category} -> {result}")
        except Exception as e:
            print(f"  ❌ {category} 매핑 오류: {e}")
            logger.error(f"TEST_ERROR: {platform_name}.{category} failed: {e}")
            success = False
    return success

def main(test_platform='arxiv'):
    mapper = UnifiedCategoryMapper()
    print(f"Starting category mapping test for {test_platform}...")
    test_platform_mapping_direct(mapper, test_platform)

if __name__ == "__main__":
    # 기본적으로 arXiv 테스트를 실행하거나, 다른 플랫폼을 인수로 전달하여 실행할 수 있습니다.
    # 예: python test_mapping.py biorxiv
    import sys
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
