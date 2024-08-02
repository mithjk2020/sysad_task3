#save and execute this script in the same dir where mystery.jpeg is stored

sudo apt-get install steghide
sudo apt-get install libimage-exiftool-perl

echo "Enter your text:"
read input_text
encoded_text=$(echo -n "$input_text" | base64)
echo "$encoded_text" > secret.txt

steghide embed -ef secret.txt -cf mystery.jpeg


#clue in metadata
exiftool -UserComment="Passphrase is secretsecret" mystery.jpeg

steghide extract -sf mystery.jpeg

