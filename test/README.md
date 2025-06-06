# Test Tools Guide

## Batch Files

### 1. quick_test.bat
**Purpose**: Quick system validation (under 1 minute)
**Usage**:
```cmd
D:\arxiv-paper-system\test\quick_test.bat
```
- Check directory structure
- Test module imports
- Verify crawler initialization
- Create output directories

### 2. run_simple_test.bat
**Purpose**: Simple crawler test (3 papers only)
**Usage**:
```cmd
D:\arxiv-paper-system\test\run_simple_test.bat
```
- Test platform crawlers
- Quick function validation
- Development debugging

### 3. run_integrated_test.bat
**Purpose**: Full pipeline test (Crawling→AI→PDF→Logging)
**Usage**:
```cmd
D:\arxiv-paper-system\test\run_integrated_test.bat
```
- Complete workflow validation
- AI analysis and PDF generation
- Notion auto-documentation

### 4. run_all_tests.bat
**Purpose**: Interactive test menu
**Usage**:
```cmd
D:\arxiv-paper-system\test\run_all_tests.bat
```
- Choose test types
- Sequential execution
- User-friendly interface

## Python Test Files

### simple_test.py
- Individual platform crawler tests
- 3 papers limit
- Interactive platform selection

### integrated_platform_test.py
- Crawling + AI analysis + PDF generation
- Notion auto-logging
- All platforms supported

## Recommended Execution Order

1. **quick_test.bat** - System validation
2. **run_simple_test.bat** - Basic function check
3. **run_integrated_test.bat** - Full feature test
4. **run_all_tests.bat** - Menu selection if needed

## Error Resolution

### Python Environment Issues
- Check virtual environment activation
- Verify required packages installed

### Module Import Errors
- Check backend directory path
- Delete __pycache__ folders and retry

### Crawler Initialization Failure
- Check internet connection
- Verify API key settings

### PDF Generation Failure
- Check output directory permissions
- Verify font file existence

## Logging

All tests log at ERROR level:
- Analysis results: NOTION_LOG
- PDF generation: PDF generation logs
- Debug info: NOTION_DEBUG

## Performance Optimization

- Limited test papers (3-5)
- No unnecessary validation processes
- Single file principle
- No hardcoding
