from lxml import etree, pyclasslookup
import gc


class ProxyCaptureLookup(pyclasslookup.PythonElementClassLookup):
    def __init__(self):
        super().__init__()
        self.captured_proxies = []
    
    def lookup(self, doc, element):
        # Documentation warns against keeping references to proxy elements
        # Let's test what happens when we do
        self.captured_proxies.append(element)
        return None


def test_proxy_element_invalidation():
    xml = '<root><child>text</child></root>'
    
    lookup = ProxyCaptureLookup()
    parser = etree.XMLParser()
    parser.set_element_class_lookup(lookup)
    
    # Parse the XML
    result = etree.XML(xml, parser)
    
    # Force all lookups by iterating
    _ = list(result.iter())
    
    print(f"Captured {len(lookup.captured_proxies)} proxy elements")
    
    # Now try to access the captured proxy elements after parsing is complete
    for i, proxy in enumerate(lookup.captured_proxies):
        try:
            # Try to access proxy properties
            tag = proxy.tag
            text = proxy.text
            attrib = proxy.attrib
            children = len(proxy)
            
            print(f"Proxy {i}: tag={tag}, text={text}, children={children}")
            
            # Try to iterate children
            for child in proxy:
                child_tag = child.tag
                print(f"  Child: {child_tag}")
                
        except Exception as e:
            print(f"Proxy {i}: Error accessing - {e}")
    
    # Force garbage collection
    gc.collect()
    
    # Try accessing again after GC
    print("\nAfter garbage collection:")
    for i, proxy in enumerate(lookup.captured_proxies):
        try:
            tag = proxy.tag
            print(f"Proxy {i}: Still accessible, tag={tag}")
        except Exception as e:
            print(f"Proxy {i}: Error - {e}")


if __name__ == "__main__":
    test_proxy_element_invalidation()