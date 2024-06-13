from Slayer_Accessory import next, end, wt
import Slayer_Graphics as gr
import Slayer_Form_Party as fp

wt()
gr.slayer_opening()
#next()
wt()
name = fp.get_name()
party = fp.form_party(name)
#next()
gr.loser_banner()
end()



