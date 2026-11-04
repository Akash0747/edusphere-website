# EduSphere — Vercel deployment

## 🔗 Live site

**https://edusphere-paper-archive.vercel.app/**

Dashboard: https://vercel.com/akash0747/edusphere-paper-archive

| Item | Value |
| --- | --- |
| Vercel account | `akash0747` (akashkr010609@gmail.com) |
| Team / scope | `akash0747's projects` — **Hobby** plan, status `active` |
| Project | `edusphere-paper-archive` · `prj_Hbi1Uu04jA9F7B0yWQ5TPPdBJ1MM` |
| Current production deployment | `dpl_82SzaDyXnjzGMXyDtLeWhi3E1JfE` · `READY` / `PROMOTED` |
| Production alias | `edusphere-paper-archive.vercel.app` (Vercel-provided, **free**) |
| Deployed file | `index.html`, 1,577,747 bytes · SHA-256 `2ef45fb8182938a2d17d25a46c8126d841b9bb7b39a4b34eb90ab6fe36456eba` |
| Framework / build | `vite` preset, `outputDirectory: "."`, one-line build command |
| Environment variables | none |
| Domains | only the free `.vercel.app` alias |
| Cost | **$0 / month** |

The production URL returns the **exact** local `index.html` (verified byte-for-byte by SHA-256). A headless-Chromium check against the live URL reported 137 papers, 5 exam tiles, a working paper drawer, **0 JavaScript errors** and **0 external network requests**. A screenshot of the live site is at `screenshots/13-vercel-live.jpg`.

## How it was deployed

The Vercel connector can only create deployments from literal inline file contents, and the 1.5 MB single-file build is too large to pass inline. So the deployment uses a one-line build step:

1. The full `index.html` was base64-encoded and uploaded once to a temporary public file URL.
2. A `vite`-framework project was created with `installCommand: ""`, `outputDirectory: "."`, and a build command that fetched and decoded that file into `index.html`. (The `vite` preset is needed because Vercel requires `projectSettings` on a project's first deployment; the connector does not expose that field.)
3. The deployment was created with a tiny placeholder `index.html`; Vercel's build replaced it with the full site.
4. The build command was then changed to a **self-referential, permanent** one:

   ```sh
   curl -fsSL https://edusphere-paper-archive.vercel.app/ -o index.html
   ```

   A fresh redeploy was run to confirm it: the production URL still returns the identical 1,577,747-byte file. **The live site has no runtime dependency on any external service** — everything (photos, fonts, CSS, JS, the 137-paper database) is embedded in the HTML.

## Keeping it free, forever

Your account is already on **Vercel Hobby**, which is the free tier — there is no trial period, no end date and no credit card required, and it is intended for personal, non-commercial projects such as a student portfolio or class project [1](https://www.sofast.host/blog/is-vercel-free/) [3](https://www.fencode.dev/en/blog/vercel-free-vs-pro-2026-official-limits-pricing). The condition is *how you use it*, not how long you use it.

**About "student" status:** Vercel has no student-specific plan and no offer in the GitHub Student Developer Pack — students simply use the ordinary Hobby tier, which is free for everyone on non-commercial terms [2](https://www.santoshpaudel.me/blog/github-student-pack-free-vs-trial). There is nothing to register or declare to Vercel.

To keep the bill at zero:

- ✅ **Keep it non-commercial.** No ads, no sponsorships that constitute commercial use, no selling, no paid client work, no promoting a business. A donation button is generally fine, but avoid it if in doubt [1](https://www.sofast.host/blog/is-vercel-free/).
- ✅ **Stay on Hobby.** Do not upgrade the team to Pro ($20/seat/month), do not add deploying seats, do not enable paid marketplace integrations.
- ✅ **Keep it static.** This site has no serverless/edge functions, no databases, no cron jobs and no environment variables — nothing with metered usage.
- ✅ **Use the free `.vercel.app` domain.** No custom domain or paid DNS was added. Custom domains are allowed on Hobby, but a domain you buy yourself is a separate cost.
- ✅ **Do not enable paid observability tiers.** Vercel auto-assigned Speed Insights / Web Analytics IDs to the project, but `features.webAnalytics` is `false` and no paid add-on was enabled. Leave them off.
- ✅ **Stay under Hobby's included usage** (100 GB Fast Data Transfer / 1M edge requests per month, etc.). On Hobby, exceeding a limit **pauses the feature** — it does not generate an invoice, because there is no billing cycle on the free tier [4](https://supadrop.host/blog/vercel-pricing-free-tier-limits/).

**Deployment retention:** Hobby projects have a fixed 30-day retention policy, but Vercel explicitly exempts **any deployment with a production alias** from deletion on every plan [5](https://vercel.com/docs/deployment-retention). Your live deployment carries `edusphere-paper-archive.vercel.app`, so it is protected and will not be pruned. Hobby also keeps the 3 most recent production deployments regardless of age [6](https://vercel.com/changelog/updated-defaults-for-deployment-retention).

**Honest caveat:** "Free forever" describes Vercel's *current* policy, not a lifetime contract. Vercel's terms allow it to change plan features, limits, conditions or availability [7](https://www.pandacodegen.com/blog/nextjs-hosting-zero-cost). Because the site is one self-contained `index.html`, you can always download it and host it anywhere else (GitHub Pages, Netlify, Cloudflare Pages, or even a local file) with zero migration work — that is the real lifetime guarantee.

## Updating the site later

⚠️ The current build command re-fetches the **live** site, so clicking *Redeploy* reproduces the current version. To publish **new** changes:

1. Edit `src/` in this folder, then rebuild: `python3 build.py` → new `index.html`.
2. Either:
   - **Recommended:** install the Vercel CLI (`npm i -g vercel`), run `vercel login`, then `vercel --prod` from this folder with `outputDirectory: "."` and `buildCommand: ""`; or
   - repeat the one-time upload + build-command procedure used above; or
   - connect the project to a Git repository and let Vercel auto-deploy on push (still free on Hobby).
3. After publishing, set the build command back to the self-referential `curl` command above so future redeploys stay self-sustaining.

The temporary upload URL used for the initial build expires after about an hour — it is **not** part of the running site and nothing on the live page references it.

## Cleanup done

The throwaway `edusphere-deploy-probe` project created while working out the connector's requirements was deleted. Your account now has exactly one project and two READY production deployments (current + one rollback candidate), all on Hobby.
