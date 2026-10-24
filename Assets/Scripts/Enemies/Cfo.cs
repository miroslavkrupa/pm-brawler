using UnityEngine;

namespace PMBrawler
{
    /// <summary>Throws budget cuts that drain your caffeine.</summary>
    public class Cfo : Thrower
    {
        protected override void Configure()
        {
            SetupBody(new Art.Look
            {
                size = new Vector2(0.9f, 1.8f),
                body = Art.Hex("#495057"),
                legs = Art.Hex("#212529"),
                head = Art.Skin,
                accent = Art.Hex("#ffd23f"),
                accessory = "suit"
            }, 80f, Team.Enemy);
            NameKey = "enemy.cfo";
            quoteKey = "quote.cfo";
            projectileKey = "proj.budget";
            projectileColor = Art.Hex("#ffd23f");
            projectileEffect = ProjectileEffect.DrainEnergy;
            attackDamage = 9f;
            attackCooldown = 2.2f;
            volley = 2;
            speed = 2f;
            score = 250;
        }
    }
}
