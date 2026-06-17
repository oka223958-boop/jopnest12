response = requests.post(...)
data     = response.json()

# مؤقتاً للـ debug
print("OPENROUTER RESPONSE:", data)

reply = data["choices"][0]["message"]["content"].strip()