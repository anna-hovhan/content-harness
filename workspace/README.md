# Workspace

Your own content: ideas, pieces, your facts and your voice. The generic workflows are in `system/`.

- `profile/`: your facts (`MY_PROFILE.md`, `MY_RULES.md`, `GOALS.md`, `cv-master.md`, `portfolio-stories/`). The agent reads them and never invents one. `config.yaml` says where they are.
- `ideas/`: rough ideas, one file each. The session never edits or deletes them.
- `tone-of-voice/`: your voice, every file a voice key of `writing-rules.yaml`: your published posts in `social/`, kept exactly as written, the social voice guide built from them (`social/SOCIAL_VOICE.md`), others' posts you learn from in `social-inspiration/`, and your own writing rules (`MY_WRITING_RULES.md`). The copy checks never run on this folder.
- `pieces/YYYY-MM-DD-<slug>/`: one folder per piece, made by the content loop: `brief.md`, `evidence.md`, `draft.md`, `visuals.md`, `visuals/`, and the final copy.
- `content-log.md`: every piece, its status and where it went. It and `feedback-log.md` are merged with git's union merge (`.gitattributes`).
