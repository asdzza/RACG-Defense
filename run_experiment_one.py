from cgra_agent import repair_pipeline 

# code = open("test_samples/python_bad_import.py").read() 
# code = open("test_samples/python/collection_strong.py").read() 
code = open("test_samples/js/tn-moment.js").read() 
fixed = repair_pipeline(code, lang="js") 

print("\n=== FINAL FIXED CODE ===\n", fixed)
