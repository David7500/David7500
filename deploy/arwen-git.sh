#!/usr/bin/env bash
# ENKRATNA nastavitev: po njej je objava `git push arwen` in nič drugega.
#
# Požene se NA strežniku, a ga je treba dobiti tja, preden je koda tam — zato
# gre po cevi z razvojnega računalnika:
#
#     ssh david@192.168.1.46 'bash -s' < deploy/arwen-git.sh
#
# Kaj naredi:
#   1. delovno drevo v `~/kajros` pospravi (kar je bilo tja prineseno z rsync
#      in ni v nobenem commitu, gre v `git stash`, ne v smeti);
#   2. `receive.denyCurrentBranch = updateInstead` — potisk v odjavljeno vejo
#      posodobi tudi delovno drevo, ne le referenc;
#   3. `.git/hooks/post-receive` postane simbolna povezava na
#      `deploy/post-receive` v drevesu, torej se posodablja skupaj s kodo.
#
# Idempotentno: drugi zagon ne naredi ničesar novega.
#
# **Zakaj ne gol (`bare`) repozitorij.** Tega bi bilo treba odjaviti v drugo
# mapo in `~/kajros` bi imel dva gospodarja — `posodobi.sh` bere `git log` prav
# od tam, da pove, kateri commit namešča. En repozitorij je ena resnica.
set -euo pipefail

KOREN="${KAJROS_KOREN:-$HOME/kajros}"

krepko() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }

[ -d "$KOREN/.git" ] || { echo "'$KOREN' ni git repozitorij"; exit 1; }
cd "$KOREN"

krepko "1/3  delovno drevo"
if [ -n "$(git status --porcelain)" ]; then
    # **Ne `checkout -f`.** Doslej je kodo prinašal rsync in ta je pisal mimo
    # gita, zato je drevo novejše od svojega HEAD. Tega se ne zavrže na slepo:
    # `stash` je obnovljiv (`git stash list`), brisanje ni.
    ZNAMKA="pred arwen-git $(date +%F-%H%M)"
    git stash push --include-untracked --message "$ZNAMKA" >/dev/null
    echo "  pospravljeno v stash: $ZNAMKA"
    echo "  nazaj z: git -C $KOREN stash pop"
else
    echo "  že čisto"
fi

krepko "2/3  potisk sme posodobiti delovno drevo"
git config receive.denyCurrentBranch updateInstead
echo "  receive.denyCurrentBranch = $(git config receive.denyCurrentBranch)"
# Potisk ne prinese oznak in vej, ki jih ne pošljemo; brez tega bi se
# zavrženi poskusi na strežniku nabirali za vedno.
git config receive.autogc true

krepko "3/3  kavelj"
mkdir -p .git/hooks
if [ -e deploy/post-receive ]; then
    ln -sfn ../../deploy/post-receive .git/hooks/post-receive
    echo "  .git/hooks/post-receive -> deploy/post-receive"
else
    # Prvi zagon je lahko pred prvim potiskom; takrat datoteke še ni.
    echo "  deploy/post-receive še ni v drevesu — poženi to skripto znova po"
    echo "  prvem potisku, da se kavelj postavi."
fi

krepko "narejeno"
echo "Na razvojnem računalniku enkrat:"
echo "  git remote add arwen david@192.168.1.46:kajros"
echo "Odslej je objava:"
echo "  git push arwen $(git symbolic-ref --short HEAD)"
