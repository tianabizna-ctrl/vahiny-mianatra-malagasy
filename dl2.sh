set -u
id(){ curl -sL --retry 3 -o "$2" "https://drive.usercontent.google.com/download?id=$1&export=download&confirm=t"; printf "%-46s %8s\n" "$2" "$(stat -c%s "$2" 2>/dev/null)"; }
id 1iBkNCEf-aAEQyxQ1RUfZTynU7WmVe4b0 RESEARCH/build_app_data.py
id 1L_DP3Kun01qPMAeeqTbw8uL4TwzU35WJ RESEARCH/pronunciation.py
id 1xDN1o3nqKnD0hF2qFQkyf5jhh2Yj-anX RESEARCH/content_quality.py
id 1Q62ZmuuYRdyJ-5oOS-I8BOPyS4uMtRNt RESEARCH/validate_content.py
id 1Mw9MReo6ncfsJwCcgR4qABotADiSw7_e RESEARCH/build_content_pack.py
id 1BX4SEvGkiRxMPQ6ax7q50bUlsQyBdFsj APP/data/content.js
id 13EU7fMLv0ppRrAxWsSi-eD_wnLLM9m5f APP/js/core.js
id 1l6efHeswZqOgAjs0pfcK-mm-BQEdqOUz APP/js/speech.js
id 1X-mtByxgH1bVYA3TPVC6A7VCK3f2DUa2 APP/js/ui.js
id 1190MWVzgpq-4Q-2a88ac4CNsF2Fhs6AX APP/js/views/course.js
id 18GyNHDAuZ5si3S1SffJbjZwqFMAyZHnZ APP/js/views/today.js
id 1pwkhAkwE3CAAz8YwxIuX9GxAGsQkTrBn APP/js/views/settings.js
id 1kk3NhcoK56cqutyuQPXSxNmZY679MMuc APP/js/views/session.js
id 1VwVQ9xipQNZh6GhsHE9TEHhUjhPfIS0_ APP/js/views/words.js
id 1hbKRoGE0Q5iRhdnfTQ3nY-uFEMJURF5R APP/js/views/review.js
id 179qirtyaGTQ59JC9OxzpL_rOWaPP__TB APP/js/views/progress.js
id 1TwFWnYgHUJcPdNUSZM8l7wzV3cAQEgxa APP/js/views/quiz.js
id 1IP1bNdxroVvQH4T0n9IPjvczb5SYbn6T APP/js/views/library.js
id 1bAah58az0khuNPQJtSXK2UeG477lQ_et APP/app.js
id 1dVAyKidQboWU5_mFBs2R0lvYeq6DLZBR APP/sw.js
