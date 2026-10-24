using UnityEngine;

namespace PMBrawler
{
    /// <summary>Throws bug reports that slow you down.</summary>
    public class Tester : Thrower
    {
        protected override void Configure()
        {
            SetupBody(new Art.Look
            {
                size = new Vector2(0.75f, 1.65f),
                body = Art.Hex("#52b788"),
                legs = Art.Hex("#2d6a4f"),
                head = Art.Skin,
                accent = Color.black,
                accessory = "glasses"
            }, 35f, Team.Enemy);
            NameKey = "enemy.tester";
            quoteKey = "quote.tester";
            projectileKey = "proj.bug";
            projectileColor = Art.Hex("#b7e4c7");
            projectileEffect = ProjectileEffect.Slow;
            attackDamage = 7f;
            attackCooldown = 1.8f;
            speed = 2.4f;
            score = 120;
        }
    }
}
