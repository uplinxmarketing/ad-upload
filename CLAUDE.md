# Uplinx Meta Manager — Claude Instructions

## Git workflow (ALWAYS follow this)

After completing any set of changes:

1. Commit all changed files to `claude/replace-app-uplinx-meta-g7hsg` with a clear commit message
2. Push to `origin claude/replace-app-uplinx-meta-g7hsg`
3. If the branch has merge conflicts with main, rebase onto main first
4. Create a pull request targeting `main` in the `uplinxmarketing/ad-upload` repo
5. Immediately merge the PR using squash merge
6. Every change must end up on `main` — never leave work only on the feature branch

Do this automatically at the end of every task without being asked.
