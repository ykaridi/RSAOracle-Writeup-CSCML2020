# RSA Oracle Challenge
###### Creator: Yonatan Karidi-Heller
###### Appeared in: CSCML 2020 CTF

## Challenge description:
Let ```n, e``` be the public parameters of some (1024-bit) RSA key-pair, and let ```d``` be the private key.

The challenge we are facing is, given some ciphertext ```ct = (pt ** e) % n``` (corresponding to a plaintext ```pt```)
and an oracle ```oracle(ciphertext) = ((decrypt(ciphertext) := (ciphertext ** d) % n) < random(7, n / 37)```
we need to decrypt ```ct``` (namely, find ```pt```) using ```2 ** 13``` (adaptive) oracle queries.

## The solution
The solution breaks down to performing the euclidean algorithm **beneath the encryption**
*(meaining we perform all operations given only the ciphertexts, while succeeding to perform meaningful manipulations on the plaintexts)*
 for some ciphertexts with co-prime plaintexts of the form ```(pt * k) % n, (pt * l) % n```.
 
#### Useful mapping
In the solution we are going to make use of the following mapping ```f(x) = (ct * (x ** e)) % n```.

Note that the plaintext corresponding to ```f(x)``` is ```(pt * x) % n```.

#### Comparing plaintexts of the mapping
Interestingly enough, we are (usually) able to compare the plaintexts corresponding to ```f(a), f(b)```, given ```a, b```.
Why is that possible?

The plaintext corresponding to ```f(a - b)``` is the subtraction of the plaintexts (done ```mod n```). 
In addition, given ```a, b``` we indeed know how to compute ```f(a), f(b)```.
Finally, our oracle leaks whether the plaintext of the ciphertext we send it is small,
thus (assuming our plaintexts are sufficiently small) we can use it to implement [a] comparison [oracle]:
- ```(pt * a) % n >= (pt * b) % n``` implies that 
  the plaintext corresponding to ```f(a - b)```, ```(pt * a - pt * b) % n```, is small 
  since ```pt * a, pt * b``` were small to begin with.

- ```(pt * a) % n < (pt * b) % n``` implies 
  the plaintext corresponding to ```f(a - b)```, ```(pt * a - pt * b) % n```, is large 
  since the subtraction overflows.
  
#### Dividing (with *"encrypted"* remainder) plaintexts of the mapping
Now that we have a comparison oracle, we are able to implement division *(efficiently)*,
since we can perform a binary search on the quotient *(logarithmic in the quotient and in particular the input)*,
and then compute the (**encrypted**) remainder by ```f(a - b * quotient)```.

#### Performing the euclidean algorithm *"beneath the encryption"*
Now that we have successfully implemented division with remainder (under the encryption)
for elements of the form ```f(a), f(b)``` we can perform the euclidean algorithm beneath the encryption as well,
that is since the extended euclidean algorithm is comprised of a series of *divmod* (division and modulo) operations. 

The only "caveat" is that the gcd itself (the result of the computation) will be *encrypted*, since our *divmod* implementation returns encrypted remainder.

It is important to notice that, even in this scenario, the extended euclidean algorithm yields us ```alpha, beta```
such that ```alpha * plaintext_a + beta * plaintext_b = gcd(plaintext_a, plaintext_b) (mod n)``` where ```plaintext_a, plaintext_b```
are (respectively) the plaintexts corresponding to ```f(a), f(b)```.

### Putting it all together
We select ```k, l``` such that ```f(k), f(l)``` have small sufficiently plaintexts (namely, ```(pt * k) % n, (pt * l) % n``` are small), 
we can check whether the corresponding plaintexts are small using our oracle.

With high probability, the plaintexts are co-prime. Thus, performing the extended euclidean algorithm
 ***beneath the encryption*** yields us ```alpha, beta``` such that ```alpha * (pt * k) + beta * (pt * l) = gcd((pt * k) % n, (pt * l) % n) = 1 (mod n)```.

In particular, ```pt * (alpha * k + beta * l) = 1 (mod n)```.

In other words, ```(alpha * k + beta * l)``` is the inverse of ```pt``` in ```Z_n``` (namely, the inverse ```mod n```),
and inverting ```mod n``` is easy - which finally allows us to find the plaintext ```ct```! (we know ```k, l, alpha, beta```)


### Remarks
I did not do the exact computation (and ignored some intricate details), but assuming the oracle "acts well" for the comparisons, this algorithm should have logarithmic complexity
(it is clear that it's complexity is at most ```O(log ** 2)```, but a more careful analysis should yield logarithmic complexity)


## Script requirements

- Python>=3.8
- pycrypto (or pycryptodome)
 