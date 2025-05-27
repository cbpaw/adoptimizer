import { Outlet } from 'react-router-dom'

export default function Root () {
  return (
    <>
      <main >
        <div className='container'>
          <Outlet />
        </div>
      </main>
    </>
  )
}
