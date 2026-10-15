# Data Flow & Workflow

## Loan application workflow

```mermaid
stateDiagram-v2
    [*] --> Sales
    Sales --> KYC: Profile saved by updateProfile
    KYC --> Credit: Aadhaar verified
    KYC --> Done: Verification rejected
    Credit --> Loan_Selection: Score and FOIR eligible
    Credit --> Done: Score or FOIR rejected
    Loan_Selection --> Done: PDF generated
```

The LangGraph agent decides when to call tools. Django tools validate each transition against stored session state and database records. The API persists user and assistant messages while redacting Aadhaar and PAN from stored logs.

## Chat and tool flow

```mermaid
sequenceDiagram
    participant User
    participant React
    participant Django
    participant Graph as LangGraph
    participant Model as Chat model
    participant Tools as Django tools
    participant DB as Django database

    User->>React: Send a message
    React->>Django: POST /api/chat/ with session cookie
    Django->>Graph: Prior messages + current message
    Graph->>Model: System context + conversation
    Model-->>Graph: Reply or tool call
    Graph->>Tools: Run requested tool(s) sequentially
    Tools->>DB: Validate and persist workflow state
    Tools-->>Graph: Tool result
    Graph->>Model: Tool result for next response
    Model-->>Django: Final assistant reply
    Django-->>React: Reply, stage, profile, and application state
```

## Document OCR

The React client uploads a JPEG, PNG, or WebP image to `POST /api/ocr/upload/`. Django validates its type and size, sends the image to Groq Vision, and returns extracted fields to the chat client. The chat agent can then use `updateProfile` or the KYC and credit tools as appropriate.

## Loan PDF

After a verified applicant passes credit and FOIR checks, `getAvailableLoans` returns products from Django's database. Once the applicant chooses one, `generateLoanPDF` confirms the selected product against the options previously returned, creates a PDF under Django media storage, and adds the download path to the session response.
