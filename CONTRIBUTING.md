# Add an entry

You need a GitHub account, `git`, and [uv](https://docs.astral.sh/uv/).

1. In the deq-tune app, open **Settings → Backup** and tap **Save to a file**.
   The file holds your own profiles and EQs.
2. Fork this repository and clone your fork.
3. Make the entry from your backup file. Name one EQ or one profile:

   ```sh
   uv run python -m tools.add_entry ~/Downloads/deq-tune-library-2026-10-24.json \
       --equalizer "Night drive" --author your-github-name \
       --description "Less bass and softer highs, for the motorway at night."
   ```

   For a car profile, use `--profile "<its name>"`. Say in the description
   which car it is for: the year, the factory audio system (for example
   Bose), and how you set it up. If the profile has no brand or car model,
   give them with `--brand` and `--model`.
4. Check it:

   ```sh
   uv run python -m tools.check
   ```

5. Commit the new file and open a pull request. The pull request runs the
   same check.

## The rules for an entry

- One item per file. The tool puts the file at the right place.
- A name that no other entry of the same kind has.
- A description that says what the entry is for. A profile's description
  names the car and its audio system.
- Values in the ranges that the app uses: EQ gains within ±12 dB, speaker
  levels from -24 to 10 dB, and speaker distances that spread no more than
  350 cm. The check refuses an entry outside them.
- Only what you made yourself. Do not add the factory presets: every
  install has them already.

By opening a pull request, you put your entry in the public domain under
[CC0 1.0](LICENSE).

## Change or remove your entry

Open a pull request that changes or deletes your file. People who added
your entry before keep their own copy: the app does not change items that
are in their library.
