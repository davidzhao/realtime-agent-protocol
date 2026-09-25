# Contributing

Thanks for your interest in improving the **Agentforce Live A2A Profile Extension**.
This repository is a *specification* project: the normative contract lives in
[`spec.md`](spec.md), supported by JSON Schemas, reference fixtures, a conformance
suite, and reference implementations. There is no published package to install.

## How to propose a change

1. **Open an issue first.** Before starting work, file an issue describing the
   problem or enhancement (use the appropriate template under
   [`.github/ISSUE_TEMPLATE`](.github/ISSUE_TEMPLATE)). This lets us track the effort,
   offer guidance, and avoid duplicated work. Spec-clarification issues are especially
   welcome — ambiguity in the prose is a defect.
2. **Discuss the design.** Normative changes (anything with MUST/SHOULD/MAY, a new
   directive, a payload field, or a state transition) should reach rough consensus in
   the issue before a PR. See [`GOVERNANCE.md`](GOVERNANCE.md) for the decision process
   and versioning rules.
3. **Fork** (external contributors) or **branch off `main`** (committers), and create a
   topic branch.
4. **Make the change consistently across artifacts.** A change to normative behavior in
   `spec.md` generally requires matching updates to the JSON Schemas (`schemas/`),
   fixtures (`fixtures/`), and the conformance suite (`conformance/`). Keep them in sync.
5. **Validate locally** before opening a PR (see below).
6. **Sign the CLA** (see [CLA](#cla)).
7. **Open a pull request** using the PR template. Describe the spec sections affected and
   confirm the conformance suite passes.

## Validating your change

The machine-checkable artifacts are validated with Python. From the repo root:

```bash
pip install -r conformance/requirements.txt   # or: pip install jsonschema pytest
pytest conformance/                            # schema + behavioral conformance tests
```

Schema and fixture changes must keep `pytest conformance/` green; CI enforces this on
every PR.

## Commit messages

We use [Conventional Commits](https://www.conventionalcommits.org/): `type: summary`.
Common types here: `spec`, `schema`, `fixtures`, `conformance`, `docs`, `chore`, `ci`.
Example: `spec: clarify sequenceId ordering across event channels`.

## CLA

External contributors are required to sign a Contributor's License Agreement. You can do
so at <https://cla.salesforce.com/sign-cla>.

## Merging

Pull request merging is restricted to squash-and-merge. Reviews are routed by
[`CODEOWNERS`](CODEOWNERS).
