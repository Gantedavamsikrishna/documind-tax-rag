# import json
# chunks = json.load(open('data/chunks/sections.json', encoding='utf-8'))
# print('Total chunks:', len(chunks))
# sections = [c['section'] for c in chunks]
# # find suspicious/garbage section labels (too long, weird patterns)
# suspicious = [s for s in sections if len(s) > 6]
# print('Suspicious section labels:', suspicious[:30])
# print('Sample of first 10 sections:', sections[:30])



# import json
# chunks = json.load(open('data/chunks/sections.json', encoding='utf-8'))
# sections = [c['section'] for c in chunks]
# lettered = [s for s in sections if any(ch.isalpha() for ch in s)]
# print('Total lettered sections found:', len(lettered))
# print('Sample:', lettered[90:200])
# print('80C present?', '80C' in sections)


# import json
# chunks = json.load(open('data/chunks/sections.json', encoding='utf-8'))
# sections = [c['section'] for c in chunks]
# print('Last 20 sections:', sections[-20:])



# import chromadb
# client = chromadb.PersistentClient(path='./chroma_db')
# collection = client.get_collection('income_tax_act')
# print('Total chunks in DB:', collection.count())
# result = collection.get(ids=['80C'])
# print('80C found:', result['documents'])


# import chromadb
# client = chromadb.PersistentClient(path='./chroma_db')
# collection = client.get_collection('income_tax_act')
# result = collection.get(ids=['2(14)'])
# print('Direct 2(14):', result['ids'], result['documents'][:1])
# all_ids = collection.get()['ids']
# matches = [i for i in all_ids if '2(14' in i or '14' in i and i.startswith('2')]
# print('IDs containing 2(14)-like pattern:', matches[:10])

# import shutil
# shutil.rmtree('chroma_db', ignore_errors=True)
# print('chroma_db deleted')


import json
data = json.load(open('data/eval/results.json'))
for r in data['results']:
    if r['question'] == 'What is section 10?':
        print(r['answer_preview'])
