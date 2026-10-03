import { StrictMode, createContext, useContext, useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import {
  BrowserRouter,
  Link,
  Navigate,
  Route,
  Routes,
  useNavigate,
  useParams,
} from 'react-router-dom'
import './styles.css'

const AuthContext = createContext(null)

const api = async (url, options = {}) => {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })

  if (response.status === 204) return null

  const data = await response.json()

  if (!response.ok) {
    throw new Error(data.error || 'Something went wrong.')
  }

  return data
}

function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api('/api/auth/me')
      .then((data) => setUser(data.user))
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  return (
    <AuthContext.Provider value={{ user, setUser, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

const useAuth = () => useContext(AuthContext)

function Navbar() {
  const { user, setUser } = useAuth()
  const navigate = useNavigate()

  const logout = async () => {
    await api('/api/auth/logout', { method: 'DELETE' })
    setUser(null)
    navigate('/login')
  }

  return (
    <header>
      <Link className="brand" to="/">
        CarePrep
      </Link>

      <nav>
        {user ? (
          <>
            <Link to="/appointments">My appointments</Link>
            <Link to="/appointments/new">New appointment</Link>
            <span>{user.email}</span>
            <button className="linkButton" onClick={logout}>
              Log out
            </button>
          </>
        ) : (
          <>
            <Link to="/login">Log in</Link>
            <Link className="button" to="/register">
              Create account
            </Link>
          </>
        )}
      </nav>
    </header>
  )
}

function Protected({ children }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <main>
        <p>Restoring your secure session…</p>
      </main>
    )
  }

  return user ? children : <Navigate to="/login" replace />
}

function AuthPage({ register = false }) {
  const { setUser, user } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (user) {
    return <Navigate to="/appointments" replace />
  }

  const submit = async (event) => {
    event.preventDefault()
    setBusy(true)
    setError('')

    try {
      const data = await api(`/api/auth/${register ? 'register' : 'login'}`, {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      })

      setUser(data.user)
      navigate('/appointments')
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="auth">
      <section className="card">
        <h1>{register ? 'Create your private workspace' : 'Welcome back'}</h1>

        <p>
          {register
            ? 'Use a password with at least eight characters.'
            : 'Log in to prepare for your appointments.'}
        </p>

        <form onSubmit={submit}>
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </label>

          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              minLength="8"
              required
            />
          </label>

          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}

          <button disabled={busy}>
            {busy ? 'Please wait…' : register ? 'Create account' : 'Log in'}
          </button>
        </form>

        <p>
          {register ? 'Already registered?' : 'New to CarePrep?'}{' '}
          <Link to={register ? '/login' : '/register'}>
            {register ? 'Log in' : 'Create an account'}
          </Link>
        </p>
      </section>
    </main>
  )
}

function Appointments() {
  const [items, setItems] = useState([])
  const [state, setState] = useState('loading')
  const [error, setError] = useState('')

  const load = () => {
    setState('loading')
    setError('')

    api('/api/appointments')
      .then((data) => {
        setItems(data.appointments)
        setState('ready')
      })
      .catch((requestError) => {
        setError(requestError.message)
        setState('error')
      })
  }

  useEffect(() => {
    load()
  }, [])

  if (state === 'loading') {
    return (
      <main>
        <p>Loading appointments…</p>
      </main>
    )
  }

  if (state === 'error') {
    return (
      <main>
        <p className="error">{error}</p>
        <button onClick={load}>Try again</button>
      </main>
    )
  }

  return (
    <main>
      <div className="pageTitle">
        <div>
          <h1>Your appointments</h1>
          <p>Keep your visit details and questions in one private place.</p>
        </div>

        <Link className="button" to="/appointments/new">
          Add appointment
        </Link>
      </div>

      {items.length === 0 ? (
        <section className="empty">
          <h2>No appointments yet</h2>
          <p>Create your first appointment, then add the questions you want to discuss.</p>
          <Link className="button" to="/appointments/new">
            Create appointment
          </Link>
        </section>
      ) : (
        <div className="grid">
          {items.map((appointment) => (
            <article className="card" key={appointment.id}>
              <p className="eyebrow">{appointment.date}</p>
              <h2>{appointment.provider}</h2>
              <p>
                {appointment.visit_type}
                {appointment.location && ` · ${appointment.location}`}
              </p>
              <Link to={`/appointments/${appointment.id}`}>
                Open preparation list →
              </Link>
            </article>
          ))}
        </div>
      )}
    </main>
  )
}

const emptyAppointment = {
  provider: '',
  visit_type: 'General visit',
  date: '',
  location: '',
  notes: '',
}

function AppointmentForm({ initial = emptyAppointment, onSave }) {
  const [form, setForm] = useState(initial)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const change = (event) => {
    setForm({
      ...form,
      [event.target.name]: event.target.value,
    })
  }

  const submit = async (event) => {
    event.preventDefault()
    setBusy(true)
    setError('')

    try {
      await onSave(form)
    } catch (requestError) {
      setError(requestError.message)
      setBusy(false)
    }
  }

  return (
    <form className="card form" onSubmit={submit}>
      <label>
        Provider or clinic
        <input
          name="provider"
          value={form.provider}
          onChange={change}
          required
        />
      </label>

      <label>
        Visit type
        <input
          name="visit_type"
          value={form.visit_type}
          onChange={change}
        />
      </label>

      <label>
        Date
        <input
          name="date"
          type="date"
          value={form.date}
          onChange={change}
          required
        />
      </label>

      <label>
        Location (optional)
        <input
          name="location"
          value={form.location}
          onChange={change}
        />
      </label>

      <label>
        Preparation notes (optional)
        <textarea
          name="notes"
          value={form.notes}
          onChange={change}
        />
      </label>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}

      <button disabled={busy}>{busy ? 'Saving…' : 'Save appointment'}</button>
    </form>
  )
}

function NewAppointment() {
  const navigate = useNavigate()

  return (
    <main>
      <h1>New appointment</h1>

      <AppointmentForm
        onSave={async (form) => {
          const data = await api('/api/appointments', {
            method: 'POST',
            body: JSON.stringify(form),
          })

          navigate(`/appointments/${data.appointment.id}`)
        }}
      />
    </main>
  )
}

function Detail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [appointment, setAppointment] = useState(null)
  const [error, setError] = useState('')
  const [question, setQuestion] = useState('')
  const [priority, setPriority] = useState(2)

  const load = () => {
    setError('')

    api(`/api/appointments/${id}`)
      .then((data) => setAppointment(data.appointment))
      .catch((requestError) => setError(requestError.message))
  }

  useEffect(() => {
    load()
  }, [id])

  if (error) {
    return (
      <main>
        <p className="error">{error}</p>
        <Link to="/appointments">Return to appointments</Link>
      </main>
    )
  }

  if (!appointment) {
    return (
      <main>
        <p>Loading appointment…</p>
      </main>
    )
  }

  const questions = appointment.questions || []

  const deleteAppointment = async () => {
    if (window.confirm('Delete this appointment and all its questions?')) {
      await api(`/api/appointments/${id}`, { method: 'DELETE' })
      navigate('/appointments')
    }
  }

  const addQuestion = async (event) => {
    event.preventDefault()

    if (!question.trim()) return

    await api(`/api/appointments/${id}/questions`, {
      method: 'POST',
      body: JSON.stringify({
        text: question,
        priority: Number(priority),
      }),
    })

    setQuestion('')
    load()
  }

  const updateQuestion = async (currentQuestion, patch) => {
    await api(`/api/questions/${currentQuestion.id}`, {
      method: 'PATCH',
      body: JSON.stringify(patch),
    })

    load()
  }

  const deleteQuestion = async (currentQuestion) => {
    if (window.confirm('Delete this question?')) {
      await api(`/api/questions/${currentQuestion.id}`, {
        method: 'DELETE',
      })

      load()
    }
  }

  return (
    <main>
      <div className="pageTitle">
        <div>
          <p className="eyebrow">{appointment.date}</p>
          <h1>{appointment.provider}</h1>
          <p>
            {appointment.visit_type}
            {appointment.location && ` · ${appointment.location}`}
          </p>
        </div>

        <div className="actions">
          <Link className="button secondary" to={`/appointments/${id}/edit`}>
            Edit
          </Link>
          <button className="danger" onClick={deleteAppointment}>
            Delete
          </button>
        </div>
      </div>

      {appointment.notes && (
        <section className="notes">
          <h2>Preparation notes</h2>
          <p>{appointment.notes}</p>
        </section>
      )}

      <section>
        <h2>Questions to discuss</h2>

        <form className="questionForm" onSubmit={addQuestion}>
          <input
            aria-label="New question"
            placeholder="Add a question for your visit"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
          />

          <select
            value={priority}
            onChange={(event) => setPriority(event.target.value)}
            aria-label="Priority"
          >
            <option value="1">Priority 1</option>
            <option value="2">Priority 2</option>
            <option value="3">Priority 3</option>
          </select>

          <button>Add question</button>
        </form>

        {questions.length === 0 ? (
          <p className="muted">
            No questions yet. Add the most important concern first.
          </p>
        ) : (
          <div className="questions">
            {questions.map((currentQuestion) => (
              <article
                className={`question ${currentQuestion.discussed ? 'done' : ''}`}
                key={currentQuestion.id}
              >
                <input
                  type="checkbox"
                  checked={currentQuestion.discussed}
                  onChange={(event) =>
                    updateQuestion(currentQuestion, {
                      discussed: event.target.checked,
                    })
                  }
                  aria-label={`Mark ${currentQuestion.text} discussed`}
                />

                <div>
                  <span className="badge">
                    Priority {currentQuestion.priority}
                  </span>
                  <p>{currentQuestion.text}</p>
                </div>

                <button
                  className="linkButton dangerText"
                  onClick={() => deleteQuestion(currentQuestion)}
                >
                  Delete
                </button>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  )
}

function Edit() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [appointment, setAppointment] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api(`/api/appointments/${id}`)
      .then((data) => setAppointment(data.appointment))
      .catch((requestError) => setError(requestError.message))
  }, [id])

  if (error) {
    return (
      <main>
        <p className="error">{error}</p>
        <Link to="/appointments">Return to appointments</Link>
      </main>
    )
  }

  if (!appointment) {
    return (
      <main>
        <p>Loading appointment…</p>
      </main>
    )
  }

  return (
    <main>
      <h1>Edit appointment</h1>

      <AppointmentForm
        initial={appointment}
        onSave={async (form) => {
          await api(`/api/appointments/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(form),
          })

          navigate(`/appointments/${id}`)
        }}
      />
    </main>
  )
}

function Home() {
  const { user } = useAuth()

  return (
    <main className="hero">
      <p className="eyebrow">Appointment preparation planner</p>
      <h1>Arrive prepared for the conversations that matter.</h1>
      <p>
        CarePrep keeps fictional appointment details and prioritized questions
        together in a private, simple workspace. It is an organizational tool,
        not a source of medical advice or real medical-record storage.
      </p>

      <Link className="button" to={user ? '/appointments' : '/register'}>
        {user ? 'View appointments' : 'Create your workspace'}
      </Link>
    </main>
  )
}

function NotFound() {
  return (
    <main>
      <h1>Page not found</h1>
      <Link to="/">Return home</Link>
    </main>
  )
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Navbar />

        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<AuthPage />} />
          <Route path="/register" element={<AuthPage register />} />
          <Route
            path="/appointments"
            element={
              <Protected>
                <Appointments />
              </Protected>
            }
          />
          <Route
            path="/appointments/new"
            element={
              <Protected>
                <NewAppointment />
              </Protected>
            }
          />
          <Route
            path="/appointments/:id"
            element={
              <Protected>
                <Detail />
              </Protected>
            }
          />
          <Route
            path="/appointments/:id/edit"
            element={
              <Protected>
                <Edit />
              </Protected>
            }
          />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>
)