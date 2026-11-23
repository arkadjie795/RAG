import json

path = r'C:\Users\arkadjie\.gemini\antigravity\brain\7ad91a73-a5eb-47ba-9496-0e358f0ee02e\.system_generated\logs\transcript.jsonl'
full_path = r'C:\Users\arkadjie\.gemini\antigravity\brain\7ad91a73-a5eb-47ba-9496-0e358f0ee02e\.system_generated\logs\transcript_full.jsonl'

target_step = None
with open(path, 'r', encoding='utf-8') as f:
    for line in f:
        obj = json.loads(line)
        if obj.get('type') == 'USER_INPUT' and 'FINAL INDEPENDENT TECHNICAL AUDIT' in obj.get('content', ''):
            target_step = obj.get('step_index')
            print('Found step:', target_step)
            print('Truncated fields:', obj.get('truncated_fields'))

if target_step is not None:
    with open(full_path, 'r', encoding='utf-8') as f:
        for line in f:
            obj = json.loads(line)
            if obj.get('step_index') == target_step:
                with open('scripts/full_user_prompt.txt', 'w', encoding='utf-8') as out:
                    out.write(obj.get('content', ''))
                print('Wrote full user prompt to scripts/full_user_prompt.txt, length:', len(obj.get('content', '')))
                break
