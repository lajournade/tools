#
# ~/.bashrc
#

# If not running interactively, don't do anything
[[ $- != *i* ]] && return

PS1='[\u@\h \W]\$ '

# [bin]
PATH=$PATH:~/.local/bin

# [.bashrc]
for f in $(find ~ -maxdepth 1 -name ".bashrc_*" -type f); do
  source $f
done
