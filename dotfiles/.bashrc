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
alias gp="git push"
alias ll="ls -la"

export IDEA_HOME="/opt/idea-IC-242.23726.103"
export JAVA_HOME="/usr/lib/jvm/java-21-openjdk"
export PATH="$IDEA_HOME/bin:$JAVA_HOME/bin:$PATH"

##-----------------------------------------------------
## shell-prompt
PS1='[\u@\h \W]\$ '
if [ -f /home/lajournade/.config/synth-shell/synth-shell-prompt.sh ] && [ -n "$(echo $- | grep i)" ]; then
  source /home/lajournade/.config/synth-shell/synth-shell-prompt.sh
fi
if [ -f /home/lajournade/.config/synth-shell/better-history.sh ] && [ -n "$(echo $- | grep i)" ]; then
  source /home/lajournade/.config/synth-shell/better-history.sh
fi

##-----------------------------------------------------
## Perso
source ~/.bashrc_perso
