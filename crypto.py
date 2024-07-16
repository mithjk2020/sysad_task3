import random
import math
def primey(n):
    if n <= 1:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True
def two_primes(start, end):
    primes = [num for num in range(start, end + 1) if primey(num)]
    any_two = random.sample(primes, 2)
    prime1, prime2 = any_two
    return prime1, prime2

start = 100
end = 3000
prime1, prime2 = two_primes(start, end)
n = prime1 * prime2
phi = (prime1 - 1)*(prime2 - 1)
e = 65537

d=0
while True:
    if (d * e) % phi ==1 and d!=e:
        break
    else:
        d+=1
key1 = (e, n)
key2 = (d, n)

#ascii encoding
def text_to_numbers(text):
    return [ord(char) for char in text]

def numbers_to_text(numbers):
    return ''.join([chr(number) for number in numbers])

def encrypt_rsa(plaintext, public_key):
    e, n = public_key
    return [(charac ** e) % n for charac in plaintext]

def decrypt_rsa(ciphertext, private_key):
    d, n = private_key
    return [(charac ** d) % n for charac in ciphertext]

input_text = "hey you all"

input_numbers = text_to_numbers(input_text)

encrypted_numbers = encrypt_rsa(input_numbers, key1)
print(f"Encrypted numbers: {encrypted_numbers}")

decrypted_numbers = decrypt_rsa(encrypted_numbers, key2)

output_text = numbers_to_text(decrypted_numbers)
print(f"Decrypted text: {output_text}")






