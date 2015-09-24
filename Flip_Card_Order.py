from aqt import mw
from aqt.reviewer import Reviewer
from anki.hooks import wrap
from aqt.utils import showInfo, tooltip

prevBottomHtml = Reviewer._bottomHTML
    
def bottomHtml(self):
    disabled = ''
    if len(self.card.note().cards()) != 2:
        # disable the button if there are multiple cards in the note
        disabled = 'disabled=disabled'
    
    html = prevBottomHtml(self)
    
    html += """
<!-- this is a hack to work around the embedded quotes. -->
<div id=acotemp>
    <span> </span><br><button %(disabled)s onclick="py.link('flipcardorder');">%(flipcardorder)s</button>
</div>
<script>
var content = $('#acotemp').html();
$('#acotemp').remove();
$('#time').parent().before('<td width=100 align=right valign=top class=stat>' + content +'</td>');
</script>  
""" % dict(flipcardorder=_("Flip Card Order"), disabled=disabled)

    return html
    
Reviewer._bottomHTML = bottomHtml

# function to handle the event when our button is clicked
def linkHandler(self, evt, _old):
    if evt == "flipcardorder":
        flipCardOrder(self)
    else:
        _old(self, evt)

Reviewer._linkHandler = wrap(Reviewer._linkHandler, linkHandler, "around")

def flipCardOrder(self):
    "Execute the flip"
    
    curCard = self.card
    otherCard = getOtherCard(self, curCard)
    
    if len(self.card.note().cards()) != 2:
        # since the button is disabled, this should never happen.
        showInfo('This note has more than two cards.\nUnable to flip.')
    else:
        # enable undo
        self.mw.checkpoint(_("Flip Card Order"))

        if curCard.queue == 0 or curCard.queue == 1:
            # If the current card is in the new or learning queue
            nconf = self.mw.col.sched._newConf(curCard)
            buryNew = nconf.get("bury", True)
            if buryNew:
                # new cards are supposed to be buried.
                self.mw.col.sched.buryCards([curCard.id])
        elif curCard.queue == 2:
            rconf = self.mw.col.sched._revConf(curCard)
            buryRev = rconf.get("bury", True)
            if buryRev:
                # reviews are supposed to be buried.
                self.mw.col.sched.buryCards([curCard.id])
            
        if otherCard.queue == -2:
            # bury the current card if the other is buried.
            self.mw.col.sched.buryCards([curCard.id])
            #unbury the other card
            otherCard.queue = otherCard.type
            otherCard.flush()
            
        self.mw.reset()
        
        # Make the other card current
        self.card = otherCard
        self.card.startTimer()
        
        self._showQuestion()
        tooltip(_("Cards Flipped."))
        
def getOtherCard(self, card):
    curId = card.id
    note = card.note()
    otherId = [c.id for c in note.cards() if c.id != curId][0]
    return self.mw.col.getCard(otherId)
