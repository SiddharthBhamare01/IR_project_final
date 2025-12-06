"""
Web Crawler - OPTIMIZED FINAL VERSION
Crawls 50 pages for better data quality and diversity.
"""

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
import sys
import json
from datetime import datetime


class DocumentSpider(CrawlSpider):
    """Optimized spider for better content extraction"""
    name = 'document_spider'

    def __init__(self, seed_url, max_pages, max_depth, *args, **kwargs):
        super(DocumentSpider, self).__init__(*args, **kwargs)
        self.start_urls = [seed_url]
        self.allowed_domains = [seed_url.split('//')[-1].split('/')[0]]
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.count = 0
        self.successful = 0
        self.failed = 0
        self.start_time = datetime.now().isoformat()

    rules = (
        Rule(LinkExtractor(allow=(), unique=True), callback='parse_item', follow=True),
    )

    def parse_item(self, response):
        """Extract clean, diverse content"""
        if self.count >= self.max_pages:
            return
        
        self.count += 1
        
        try:
            # Extract title
            title = (
                response.xpath('//h1[@id="firstHeading"]//text()').get() or
                response.xpath('//h1[@class="firstHeading"]//text()').get() or
                response.xpath('//h1/text()').get() or
                response.xpath('//title/text()').get() or
                'Untitled'
            )
            
            # Extract main content - more comprehensive
            content_paragraphs = response.xpath(
                '//div[@id="mw-content-text"]//div[@class="mw-parser-output"]/p[not(ancestor::table)]//text() |'
                '//div[@id="bodyContent"]//p[not(ancestor::table) and not(ancestor::div[@class="navbox"])]//text() |'
                '//article//p[not(ancestor::nav) and not(ancestor::aside)]//text()'
            ).getall()
            
            # Clean content
            cleaned_paragraphs = []
            for text in content_paragraphs:
                text = text.strip()
                # More lenient filtering
                if (len(text) > 20 and 
                    not text.startswith('[') and 
                    'wikipedia' not in text.lower()[:20] and
                    'edit' not in text.lower()[:10]):
                    cleaned_paragraphs.append(text)
            
            content = ' '.join(cleaned_paragraphs)
            content = ' '.join(content.split())  # Remove extra whitespace
            
            # More lenient validation
            if not content or len(content) < 150:
                self.logger.warning(f"Insufficient content: {title} ({len(content)} chars)")
                self.failed += 1
                return
            
            # Keep more content for better indexing
            if len(content) > 5000:
                content = content[:5000]
            
            self.successful += 1
            self.logger.info(f"SUCCESS [{self.successful}/{self.max_pages}] {title[:50]} ({len(content)} chars)")
            
            yield {
                'title': title,
                'content': content,
                'url': response.url,
                'timestamp': datetime.now().isoformat()
            }
            
            # Save with better formatting
            with open('natural.txt', 'a', encoding='utf-8') as f:
                # Format: Title on own line, then content
                f.write(f'{title}\n{content}\n\n')
                
        except Exception as e:
            self.logger.error(f"Error: {response.url}: {e}")
            self.failed += 1
    
    def closed(self, reason):
        """Save statistics"""
        stats = {
            'total_pages': self.count,
            'successful_pages': self.successful,
            'failed_pages': self.failed,
            'success_rate': f"{(self.successful/self.count*100) if self.count > 0 else 0:.1f}%",
            'start_time': self.start_time,
            'end_time': datetime.now().isoformat(),
            'close_reason': reason
        }
        
        with open('crawl_stats.json', 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
        
        self.logger.info(f"\n{'='*80}")
        self.logger.info(f"CRAWLING COMPLETED")
        self.logger.info(f"  Successful: {self.successful}/{self.count} ({stats['success_rate']})")
        self.logger.info(f"  Failed: {self.failed}/{self.count}")
        self.logger.info(f"{'='*80}\n")


def run_spider(seed_url, max_pages, max_depth):
    """Run crawler with optimized settings"""
    print(f"\n{'='*80}")
    print(f"STARTING WEB CRAWLER - OPTIMIZED")
    print(f"{'='*80}")
    print(f"Target: {seed_url}")
    print(f"Max Pages: {max_pages} | Max Depth: {max_depth}")
    print(f"{'='*80}\n")
    
    process = CrawlerProcess(settings={
        'LOG_LEVEL': 'INFO',
        'CLOSESPIDER_PAGECOUNT': max_pages,
        'DEPTH_LIMIT': max_depth,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'CONCURRENT_REQUESTS': 16,  # Increased for faster crawling
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 0.5,  #1.0 More aggressive
        'AUTOTHROTTLE_START_DELAY': 2,  # 2 Faster start
        'AUTOTHROTTLE_MAX_DELAY': 30,  # 30 Lower max delay
        'AUTOTHROTTLE_DEBUG': True,
        'DOWNLOAD_TIMEOUT': 30,
        'RETRY_TIMES': 3,
        'ROBOTSTXT_OBEY': True,
        'COOKIES_ENABLED': False,
    })
    
    process.crawl(DocumentSpider, seed_url=seed_url, max_pages=max_pages, max_depth=max_depth)
    process.start()
    
    print(f"\n{'='*80}")
    print(f"CRAWLING COMPLETED!")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    seed_url = sys.argv[1] if len(sys.argv) > 1 else 'https://en.wikipedia.org/wiki/Natural_language_processing'
    max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 50  # Increased to 50
    max_depth = int(sys.argv[3]) if len(sys.argv) > 3 else 4   # Increased depth
    
    run_spider(seed_url, max_pages, max_depth)