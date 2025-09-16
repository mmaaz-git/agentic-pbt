import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

import inspect
import tokenizers.decoders as decoders

# Focus on key decoders
decoder_classes = [
    decoders.BPEDecoder,
    decoders.ByteFallback, 
    decoders.ByteLevel,
    decoders.Metaspace,
    decoders.WordPiece,
    decoders.Replace,
    decoders.Sequence,
    decoders.Strip,
    decoders.Fuse,
    decoders.CTC
]

for decoder_cls in decoder_classes:
    print(f"\n{'='*60}")
    print(f"CLASS: {decoder_cls.__name__}")
    print(f"{'='*60}")
    
    # Get docstring
    if decoder_cls.__doc__:
        print("DOCSTRING:")
        print(decoder_cls.__doc__)
    
    # Try to get init signature
    try:
        sig = inspect.signature(decoder_cls.__init__)
        print(f"\nINIT SIGNATURE: {sig}")
    except:
        print("\nINIT SIGNATURE: Could not retrieve")
    
    # Try to get decode method
    if hasattr(decoder_cls, 'decode'):
        try:
            decode_sig = inspect.signature(decoder_cls.decode)
            print(f"\nDECODE SIGNATURE: {decode_sig}")
        except:
            print("\nDECODE: Method exists but could not get signature")
    
    # Check for decode_stream method
    if hasattr(decoder_cls, 'decode_stream'):
        print("\nHAS decode_stream method")
    
    # Check for decode_chain method
    if hasattr(decoder_cls, 'decode_chain'):
        print("\nHAS decode_chain method")