import { Outlet } from 'react-router-dom'

export default function DragonKeeperLayout() {
  return (
    <div className="dk-layout" style={{ maxWidth: '1600px' }}>
      <Outlet />
    </div>
  )
}
