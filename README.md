# OTP PWN

OTP PWN can assist in the exploitation of the one-time pad (OTP) key reuse vulnerability. 

## Usage

`python otp_pwn.py [encrypted_file] [key_length]`

* encrypted_file: file containing the ciphertext that was created using a repeating keystream
* key_length: length of the keystream that is repeated

The script spawns an environment similarly to vim. The main window allows you to browse and inspect the contents of the encrypted file using the up and down arrow keys or `k` and `j` respectiveley. The following shortcuts are available:
* `j`: scroll down
* `k`: scroll up
* `u`: revert the last plaintext guess
* `m`: switch between showing the orignal file and applying the decryption key
* `n`: change the offset of the last entered plaintext by +1
* `N`: change the offset of the last entered plaintext by -1
* `g`: jump to the start of the file
* `G`: jump to the end of the file

The `n` and `N` shortcuts enable crib dragging as you can enter a plaintext guess and shift it around the ciphertext until another block decrypts to something useful.

You can switch into the command mode typing `:` which enables the following commands:

* `q`: quit 
* `p [offset] [plaintext]`: apply a plaintext guess starting at the given offset
* `phex [offset] [plaintext]`: as `p` but the plaintext input is encoded in hex
* `d [filename]`: dump the file decrypted with the derived key to a file 

## Examples

### Two messages encrypted with the same keystream

In this example, we have the following two messages:

```
Hey, let's see whether you can figure out the plaintext for this message using crib dragging!
This is another message that was encrypted using the same keystream, which makes it insecure.
```

Both messages are encrypted under the same keystream using XOR. The file `example/messages.txt.enc` contains the ciphertext of the second message appended to the end of the ciphertext of the first message. This way, we can immediateley use the file as input to the `otp_pwn.py` utility. We first figure out the length of the keystream, which is 93 in this case. Now we just have to guess some plaintext of the first or the second message e.g., `:p 0 message` and drag it along the ciphertext with the `n` and `N` shortcuts. After some more guessing, we are able to recover the keystream: 

```
bc e5 c2 8a f2 04 7d fd 3d c0 c4 57 67 4d f8 31 44 4a cb 60 25 af cd 6e b0 d1 75 79 28 95 de 5b 14 2b ce f5 46 c0 49 4f 4d dc 8c c9 b8 8a 80 69 bd 42 0d 13 d8 d8 aa be a9 45 d8 98 6a b0 22 f0 f8 96 11 e3 f4 42 5a 4b 98 d0 ff 17 2c e1 5b 31 1d b1 9f 32 59 fe 85 8d 08 20 cf 60 4a
```

### PDF file encrypted with a repeating keystream