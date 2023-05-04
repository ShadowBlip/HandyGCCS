# Enable EC write
modprobe -r ec_sys
modprobe ec_sys write_support=1
    
# Path
ECIO_PATH=/sys/kernel/debug/ec/ec0/io
    
# Takeover Register offset
EC_REG=241
    
# Values
TAKE_OVER="\064" 
GIVE_BACK="\000"

# Define a function to write to EC
write_to_ec () {
  echo -n -e $2 | dd of=$ECIO_PATH bs=1 seek=$1 count=1 conv=notrunc
}

# Set turbo button to output keyboard macro
do_takeover () {
  write_to_ec $EC_REG $TAKE_OVER
}

# Set turbo button to normal operation
do_giveback () {
  write_to_ec $EC_REG $GIVE_BACK
}

if [[ $1 == "enable" ]]; then
  do_takeover
elif [[ $1 == "disable" ]]; then
  do_giveback
fi
