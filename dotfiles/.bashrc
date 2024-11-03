#
# ~/.bashrc
#

# If not running interactively, don't do anything
[[ $- != *i* ]] && return

alias ls='ls --color=auto'
alias grep='grep --color=auto'
alias vi="nvim"
alias gs="git status"
alias gl="git log"
alias gc="git checkout"
alias gb="git branch"
alias ga="git add"

PS1='[\u@\h \W]\$ '

source ~/.bashrc_perso
