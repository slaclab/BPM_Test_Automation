# BPM_Test_Automation
Automated BPM Test Interface on lcls-dev3, featuring FRU programming, SNR &amp; RF power test, attenuation linearity test, beam resolution, and calibration signal check. 

Once at SLAC, and SSH into lcls-dev3 using [moba-xterm](https://mobaxterm.mobatek.net/) or equivalent. Moba-Xterm is recommended because you can transfer files easily, and it is free. 

<pre> <code>ssh -XY lcls-dev3</code> </pre>

or just open a session on lcls-dev3 by clicking on
session -> SSH -> type in Remote Host -> OK

In your home directory, clone this repository locally. 

Make sure that you are in bash by typing: 

<pre> <code>bash </code> </pre>

If you have not sourced the environment shell script, python would not work for you at all on lcls-dev3.  So to ensure this, you only have to do this once. 

In your home directory, open and edit the .bashrc file: 

<pre> <code>gedit .bashrc </code> </pre>

A text editor will pop up, and add the following line to the end of the .bashrc file, save it, and exit. 

<pre> <code>source /afs/slac/g/lcls/tools/script/ENVS64.bash </code> </pre>


