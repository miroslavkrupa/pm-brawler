using System.Collections.Generic;
using UnityEngine;

namespace PMBrawler
{
    public enum Lang { CS, EN }

    /// <summary>
    /// Tiny localization table. Keys map to (Czech, English). Values containing '|'
    /// are lists of variants; use Loc.Random to pick one.
    /// </summary>
    public static class Loc
    {
        const string PrefKey = "lang";

        static Lang? current; // loaded lazily: PlayerPrefs must not be touched from a static initializer

        public static Lang Current
        {
            get => current ??= (Lang)PlayerPrefs.GetInt(PrefKey, (int)Lang.CS);
            set { current = value; PlayerPrefs.SetInt(PrefKey, (int)value); PlayerPrefs.Save(); }
        }

        public static void Toggle() => Current = Current == Lang.CS ? Lang.EN : Lang.CS;

        public static string Get(string key)
        {
            if (!Table.TryGetValue(key, out var t)) return key;
            return Current == Lang.CS ? t.cs : t.en;
        }

        public static string Get(string key, params object[] args) => string.Format(Get(key), args);

        public static string Random(string key)
        {
            var options = Get(key).Split('|');
            return options[UnityEngine.Random.Range(0, options.Length)];
        }

        static readonly Dictionary<string, (string cs, string en)> Table = new()
        {
            // --- UI ---
            ["ui.title"] = ("PROJEKŤÁK: TERMÍN BYL VČERA", "PROJECT MANAGER: DUE YESTERDAY"),
            ["ui.subtitle"] = ("Doruč projekt. Přežij stakeholdery.", "Deliver the project. Survive the stakeholders."),
            ["ui.pressStart"] = ("Stiskni ENTER pro start", "Press ENTER to start"),
            ["ui.pressStart.touch"] = ("Klepni pro start", "Tap to start"),
            ["ui.controls"] = (
                "Pohyb: A/D nebo šipky   Skok: mezerník/W   Útok: J   Ganttův úder: K   Proberme to mimo poradu: L   Pauza: Esc   Celá obrazovka: F",
                "Move: A/D or arrows   Jump: Space/W   Attack: J   Gantt slam: K   Let's take this offline: L   Pause: Esc   Fullscreen: F"),
            ["ui.lang"] = ("Jazyk: čeština  [Tab = English]", "Language: English  [Tab = čeština]"),
            ["ui.hp"] = ("Zdraví", "Health"),
            ["ui.energy"] = ("Kofein", "Caffeine"),
            ["ui.lives"] = ("Životy: {0}", "Lives: {0}"),
            ["ui.score"] = ("Skóre: {0}", "Score: {0}"),
            ["ui.best"] = ("Rekord: {0}", "Best: {0}"),
            ["ui.remaining"] = ("Zbývá blokerů: {0}", "Blockers left: {0}"),
            ["ui.exitOpen"] = ("Schváleno! Běž k východu >>", "Signed off! Head to the exit >>"),
            ["ui.paused"] = ("PAUZA — porada se protáhla", "PAUSED — the meeting ran over"),
            ["ui.pausedSub"] = ("Esc = pokračovat   Tab = jazyk", "Esc = resume   Tab = language"),
            ["ui.pausedSub.touch"] = ("Klepni na > pro pokračování", "Tap > to resume"),
            ["ui.rotate"] = ("Otoč telefon na šířku", "Turn your phone sideways"),
            ["touch.attack"] = ("ÚTOK", "HIT"),
            ["ui.gameover"] = ("PROJEKT ZRUŠEN", "PROJECT CANCELLED"),
            ["ui.gameoverSub"] = ("ENTER = zkusit znovu od tohoto sprintu", "ENTER = retry from this sprint"),
            ["ui.gameoverSub.touch"] = ("Klepni = zkusit znovu od tohoto sprintu", "Tap = retry from this sprint"),
            ["ui.levelComplete"] = ("MILNÍK SPLNĚN", "MILESTONE REACHED"),
            ["ui.continue"] = ("ENTER = pokračovat", "ENTER = continue"),
            ["ui.continue.touch"] = ("Klepni = pokračovat", "Tap to continue"),
            ["ui.victory"] = ("PROJEKT DORUČEN!", "PROJECT DELIVERED!"),
            ["ui.victorySub"] = ("V termínu a v rozpočtu... zhruba.", "On time and on budget... more or less."),
            ["ui.victoryHint"] = ("ENTER = nový projekt", "ENTER = new project"),
            ["ui.victoryHint.touch"] = ("Klepni = nový projekt", "Tap = new project"),
            ["ui.status.slow"] = ("Zpomalen", "Slowed"),
            ["ui.status.reverse"] = ("Obrácené ovládání!", "Controls reversed!"),
            ["ui.status.gantt"] = ("Ganttův diagram: 2× poškození", "Gantt chart: 2× damage"),
            ["ui.status.freeze"] = ("Rozsah zmrazen", "Scope frozen"),
            ["ui.exit"] = ("VÝCHOD", "EXIT"),
            ["ui.exitLocked"] = ("ČEKÁ NA\nSCHVÁLENÍ", "AWAITING\nSIGN-OFF"),

            // --- Levels ---
            ["level1.title"] = ("Sprint 1: Vývojový tým", "Sprint 1: The Dev Team"),
            ["level1.sub"] = ("Říkali dva týdny. Jsou to čtyři.", "They said two weeks. It's been four."),
            ["level2.title"] = ("Sprint 2: Ulička testerů", "Sprint 2: The QA Gauntlet"),
            ["level2.sub"] = ("Každá oprava zrodí dvě nové chyby.", "Every fix spawns two new bugs."),
            ["level3.title"] = ("Workshop sladění stakeholderů", "Stakeholder Alignment Workshop"),
            ["level3.sub"] = ("Každý chce „jen jednu malou změnu“.", "Everyone wants \"just one small change\"."),
            ["level4.title"] = ("Řídicí výbor", "The Steering Committee"),
            ["level4.sub"] = ("Scházejí se jednou za měsíc. Dnes je ten den.", "They meet once a month. Today is that day."),
            ["level5.title"] = ("Vedení firmy", "The C-Suite"),
            ["level5.sub"] = ("CEO si v letadle přečetl článek o AI.", "The CEO read an article about AI on the plane."),

            // --- Enemy names ---
            ["enemy.dev"] = ("Vývojář", "Developer"),
            ["enemy.tester"] = ("Tester", "Tester"),
            ["enemy.stake"] = ("Stakeholder", "Stakeholder"),
            ["enemy.cfo"] = ("Finanční ředitel", "CFO"),
            ["enemy.committee"] = ("Řídicí výbor", "Steering Committee"),
            ["enemy.ceo"] = ("Generální ředitel", "CEO"),

            // --- Enemy quotes ---
            ["quote.dev"] = (
                "U mě to funguje!|To není bug, to je feature.|Odhad? Dva týdny.|Kdo tohle psal? ...Aha, já.|Musíme to celé přepsat.",
                "Works on my machine!|It's not a bug, it's a feature.|Estimate? Two weeks.|Who wrote this? ...Oh, me.|We need to rewrite everything."),
            ["quote.dev.shield"] = ("U MĚ TO FUNGUJE!", "WORKS ON MY MACHINE!"),
            ["quote.tester"] = (
                "Nejde zreprodukovat? Mně jo!|Tiket #4096 znovu otevřen.|Zkoušel jsi to v Internet Exploreru?|Závažnost: blokující.",
                "Can't reproduce? I can!|Ticket #4096 reopened.|Have you tried Internet Explorer?|Severity: blocker."),
            ["quote.stake"] = (
                "Jen jedna malinká změna!|Může to víc zářit?|Synovec by to udělal za víkend.|Myslel jsem, že to bude modré.",
                "Just one tiny change!|Can we make it pop more?|My nephew could build this in a weekend.|I thought it would be blue."),
            ["quote.stake.charge"] = ("ROZŠÍŘENÍ ROZSAHU!", "SCOPE CREEP!"),
            ["quote.cfo"] = (
                "Škrt v rozpočtu!|Je to CAPEX, nebo OPEX?|Na to chci business case.|Zvládněte to s polovičním týmem.",
                "Budget cut!|Is that CAPEX or OPEX?|I'll need a business case for that.|Do it with half the team."),
            ["quote.committee"] = (
                "Naplánujme schůzku o schůzce.|Chceme víc status reportů.|Vraťme se k požadavkům.|Kdo je tady vlastník rizika?",
                "Let's schedule a meeting about the meeting.|We need more status reports.|Let's revisit the requirements.|Who owns this risk?"),
            ["quote.committee.summon"] = ("ESKALACE!", "ESCALATION!"),
            ["quote.committee.slam"] = ("STATUS REPORT!", "STATUS REPORT!"),
            ["quote.ceo"] = (
                "Synergie!|Buďme agilnější. Rychleji.|Četl jsem o tom na LinkedInu.|Přidejte tam AI.",
                "Synergy!|Let's be more agile. Faster.|I read about this on LinkedIn.|Make it AI-powered."),
            ["quote.ceo.pivot"] = ("PIVOT!", "PIVOT!"),
            ["quote.ceo.phase2"] = ("Nové strategické priority!", "New strategic priorities!"),
            ["quote.ceo.summon"] = ("Nová strategická iniciativa!", "New strategic initiative!"),

            // --- Player ---
            ["pm.special"] = ("Proberme to mimo poradu!", "Let's take this offline!"),
            ["pm.heavy"] = ("GANTTŮV ÚDER!", "GANTT SLAM!"),
            ["pm.respawn"] = ("Poučení z chyb zapsáno.", "Lessons learned logged."),
            ["pm.noEnergy"] = ("Málo kofeinu...", "Not enough caffeine..."),
            ["pm.blocked"] = ("Zablokováno!", "Blocked!"),

            // --- Pickups ---
            ["pickup.coffee"] = ("Káva! +zdraví +kofein", "Coffee! +health +caffeine"),
            ["pickup.gantt"] = ("Ganttův diagram! 2× poškození", "Gantt chart! 2× damage"),
            ["pickup.freeze"] = ("ZMRAZENÍ ROZSAHU!", "SCOPE FREEZE!"),

            // --- Projectiles ---
            ["proj.bug"] = ("BUG", "BUG"),
            ["proj.invite"] = ("PORADA", "MEETING"),
            ["proj.budget"] = ("-Kč", "-$"),
            ["proj.memo"] = ("MEMO", "MEMO"),

            // --- Comic hit words ---
            ["fx.hit"] = ("BUM!|PRÁSK!|ŠMIK!|BÁC!|ŽUCH!", "POW!|BAM!|WHACK!|KAPOW!|THWACK!"),
            ["fx.ko"] = ("PŘEŘAZEN NA JINÝ PROJEKT", "REASSIGNED TO ANOTHER PROJECT"),
        };
    }
}
