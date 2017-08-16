# OTP PWN

OTP PWN can assist in the exploitation of the one-time pad (OTP) key reuse vulnerability. 

## Usage

`python otp_pwn.py [encrypted_file] [key_length]`

* encrypted_file: file containing the ciphertext that was created using a repeating keystream
* key_length: length of the keystream that is repeated

The script spawns an environment similarly to vim. The main window allows you to browse and inspect the contents of the encrypted file using the up and down arrow keys or `k` and `l` respectiveley. The following shortcuts are available:
* `j`: scroll down
* `k`: scroll up
* `u`: revert the last key change
* `m`: switch between applying the current key to the file or displaying the original file

You can switch into the command mode typing `:`. The following commands are available:

* `q`: quit 
* `p [offset] [plaintext]`: apply a plaintext guess starting at the given offset
* `phex [offset] [plaintext]`: as `p` but the plaintext input is encoded in hex
* `d [filename]`: dump the file decrypted with the derived key into a file 

## Examples

### Two messages encrypted with the same keystream


### PDF file encrypted with a repeating keystream