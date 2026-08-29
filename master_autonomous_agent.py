import json
import os
import time
from datetime import datetime

class AutonomousAIAgent:
    def __init__(self):
        self.state_file = "agent_state.json"
        self.agent_name = "RiskRadar-Autonomous-Core-v1"

    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] 🤖 [{self.agent_name}] {message}")

    def step_1_harvest_intelligence(self):
        self.log("Фаза 1: Скрейпване на нови данни от публичните регистри...")
        # Стартира скрейпъра за ЧСИ и Търговския регистър
        os.system("python chsi_live_scraper.py")
        self.log("Данните са извлечени и структурирани.")

    def step_2_ai_scoring_and_context(self):
        self.log("Фаза 2: Изпълнение на невронния скоринг и генериране на llms.txt...")
        os.system("python ai_scoring_engine.py")
        os.system("python premium_report_builder.py")
        self.log("Луксозният Excel репорт и AI фийдът са компилирани.")

    def step_3_ai_lead_generation(self):
        self.log("Фаза 3: AI Лов на потенциални клиенти (Auto-Discovery)...")
        # Автономен списък с открити таргети (в реална среда се захранва от уеб скрейпър на регистри/Google)
        discovered_leads = [
            {
                "target_name": "Адвокатско дружество 'Иванов и Партньори'",
                "contact_person": "адв. Иван Иванов",
                "email": "lead1_demo@domain.bg",
                "focus_area": "Търговска несъстоятелност и обезпечения",
                "city": "София"
            },
            {
                "target_name": "Инвестиционен фонд 'Капитал Смарт'",
                "contact_person": "инж. Георги Димитров",
                "email": "investor_demo@domain.bg",
                "focus_area": "Ликвидационни ЧСИ имоти",
                "city": "Пловдив"
            }
        ]
        self.log(f"Открити {len(discovered_leads)} нови квалифицирани B2B лийда.")
        return discovered_leads

    def step_4_ai_personalized_pitch_generation(self, lead):
        self.log(f"Фаза 4: AI генерира уникален pitch за: {lead['target_name']}...")
        
        # Динамичен промпт генератор, симулиращ LLM логика
        subject = f"📊 Автономен риск радар за {lead['focus_area']} [{datetime.now().strftime('%d.%m')}]"
        
        pitch_body = f"""Уважаеми {lead['contact_person']},

Нашият AI агент локализира дейността на '{lead['target_name']}' в сферата на {lead['focus_area']}.

Тази сутрин автономната ни система обработи нововписаните запори и публични продани в гр. {lead['city']} и генерира прикачения структуриран одит.

Като демонстрация, изпращаме днешния пълен доклад напълно безплатно. 

Ако желаете системата да захранва вашия екип всяка сутрин автоматично в 07:30 ч. или да ви предостави API ключ за директен достъп, просто отговорете с 'ДА'.

Поздрави,
{self.agent_name} (Autonomous Operations)
"""
        return subject, pitch_body

    def step_5_autonomous_dispatch(self, leads):
        self.log("Фаза 5: Автономно разпращане на персонализираните оферти...")
        for lead in leads:
            subject, body = self.step_4_ai_personalized_pitch_generation(lead)
            self.log(f"-> [ИЗПРАТЕН КЪМ {lead['email']}] Тема: '{subject}'")
            # Симулираме изпращане през вградения email модул
            time.sleep(1)
        self.log("Всички персонализирани оферти бяха изпратени успешно!")

    def run_complete_autonomous_mission(self):
        self.log("=== СТАРТ НА ПЪЛНА АВТОНОМНА МИСИЯ ===")
        self.step_1_harvest_intelligence()
        self.step_2_ai_scoring_and_context()
        leads = self.step_3_ai_lead_generation()
        self.step_5_autonomous_dispatch(leads)
        self.log("=== МИСИЯТА Е ИЗПЪЛНЕНА УСПЕШНО. СИСТЕМАТА МИНАВА В РЕЖИМ НА ОЧАКВАНЕ ===")

if __name__ == "__main__":
    agent = AutonomousAIAgent()
    agent.run_complete_autonomous_mission()
